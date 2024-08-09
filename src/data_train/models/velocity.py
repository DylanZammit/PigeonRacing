import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_squared_error

import lightgbm as lgb

import numpy as np
import os

from data_train.models.generic import Model
from data_train.utils import load_data
from src import MODEL_PATH

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 200)


class VelocityModel(Model):

    def plot(self):
        model = self.model
        lgb.plot_metric(model.evals_result_)
        plt.figure()

        y_pred = model.predict(self.df_x_train)

        train_rmse = np.sqrt(mean_squared_error(y_pred, self.y_train))

        plt.hexbin(y_pred, self.y_train)
        plt.xlabel('Prediction')
        plt.ylabel('True Value')
        plt.title(f'Velocity prediction: Train data (RMSE={train_rmse: .2f})')

        plt.figure()

        y_pred = model.predict(self.df_x_test)

        test_rmse = np.sqrt(mean_squared_error(y_pred, self.y_test))

        plt.hexbin(y_pred, self.y_test)
        plt.title(f'Velocity prediction: Test data (RMSE={test_rmse: .2f})')

        lgb.plot_importance(model)
        lgb.plot_importance(model, importance_type="gain")
        plt.show()

        feature_importances = {f: imp for imp, f in zip(model.feature_importances_, model.feature_name_)}

        # TODO: use log instead of print
        print(dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True)))

    def clean(self) -> pd.DataFrame:
        return self.df[
            (self.df.total_race_count > 1) &
            (self.df.velocity > 50)
        ]


def main() -> None:

    df_race_results_final = load_data('df_race_results_final')

    vm = VelocityModel(df_race_results_final, 'velocity_params.yaml')
    vm.fit()
    vm.plot()
    vm.save_pickle(os.path.join(MODEL_PATH, 'velocity.pkl'))


if __name__ == '__main__':
    main()
