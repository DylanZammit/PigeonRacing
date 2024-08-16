from sklearn.preprocessing import LabelEncoder

import mlflow
import lightgbm as lgb
import pandas as pd
import os
from src import PARAMS_PATH
import pickle
import yaml


# TODO: data should be in DB and this should be calculated once
def calculate_pigeon_form(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(['pigeon_id', 'release_datetime']).reset_index(drop=True)
    df['velocity_lag'] = df.groupby('pigeon_id').velocity.shift()
    df['race_count'] = df.groupby('pigeon_id').velocity_lag.cumcount()
    df['total_race_count'] = df.groupby('pigeon_id').pigeon_id.transform('count')
    df['velocity_form'] = df.groupby('pigeon_id').velocity_lag.ewm(
        halflife='60 days', times=pd.DatetimeIndex(df.release_datetime)
    ).mean().values
    df['velocity_form_linear'] = df.groupby('pigeon_id').velocity_lag.expanding().mean().values
    return df


class Model:
    def __init__(self, df: pd.DataFrame, config: str):
        """

        Parameters
        ----------
        df: pd.DataFrame
            DataFrame containing all features and prediction columns
        config: str
            Yaml file name containing model parameters
        """
        with open(os.path.join(PARAMS_PATH, config), 'r') as f:
            config = yaml.safe_load(f)

        self.pred_col = config['pred_col']
        self.param = config['model_params']
        self.train_start = pd.Timestamp(config['train_start'])
        self.train_end = pd.Timestamp(config['train_end'])
        self.covariates = config['features']['covariates']
        self.categorical = config['features']['categorical']

        self.df = calculate_pigeon_form(df)
        self.df['arrived'] = ~self.df.arrival_datetime.isna()
        self.df['arrival_datetime'] = pd.to_datetime(self.df['arrival_datetime'], unit='ms', errors='ignore')
        self.df['release_datetime'] = pd.to_datetime(df['release_datetime'])
        self.df = self.clean()

        self.df_x_train, self.df_x_test, self.y_train, self.y_test = self.train_test_split()
        self._model = None

    def clean(self) -> pd.DataFrame:
        return self.df

    @property
    def model(self):
        if hasattr(self, '_model'):
            return self._model

        print('Run fit() method first')

    def train_test_split(self):
        important_features = self.categorical + self.covariates  # comment if we want specific features

        important_categorical = list(set(self.categorical) & set(important_features))
        important_covariates = list(set(self.covariates) & set(important_features))

        label_encoders = {}
        for c in important_categorical:
            label_encoder = LabelEncoder()
            self.df.loc[:, c] = label_encoder.fit_transform(self.df[c])
            label_encoders[c] = label_encoder

        self.df[important_categorical] = self.df[important_categorical].astype(float)
        df_xy_train = self.df[
            (self.df.release_datetime >= self.train_start) &
            (self.df.release_datetime < self.train_end)
        ]

        df_xy_test = self.df[self.df.release_datetime >= self.train_end]

        df_x_train = df_xy_train[important_categorical + important_covariates]
        y_train = df_xy_train[self.pred_col]

        df_x_test = df_xy_test[important_categorical + important_covariates]
        y_test = df_xy_test[self.pred_col]
        return df_x_train, df_x_test, y_train, y_test

    def fit(self):
        lgbm = lgb.LGBMRegressor if self.param['objective'] == 'regression' else lgb.LGBMClassifier
        model = lgbm(**self.param)
        mlflow.lightgbm.autolog()
        with mlflow.start_run():
            model.fit(
                self.df_x_train, self.y_train,
                eval_set=[(self.df_x_test, self.y_test), (self.df_x_train, self.y_train)]
            )
        self._model = model
        return model

    def plot(self):
        raise NotImplementedError('Implement plot method in customer class')

    def save_pickle(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
