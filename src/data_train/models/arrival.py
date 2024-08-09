import pandas as pd
import matplotlib.pyplot as plt

import lightgbm as lgb
from sklearn.metrics import RocCurveDisplay, classification_report, confusion_matrix
import os

from data_train.models.generic import Model
from data_train.utils import load_data
from src import MODEL_PATH

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 200)


class ArrivalModel(Model):

    def plot(self):
        model = self.model
        lgb.plot_metric(model)
        y_pred_train = model.predict_proba(self.df_x_train)[:, 1]
        y_pred = model.predict_proba(self.df_x_test)[:, 1]
        t = 0.7

        print('------------ TRAIN DATA ------------')
        print(classification_report(self.y_train, y_pred_train > t))
        print(confusion_matrix(self.y_train, y_pred_train > t))

        print('------------ TEST DATA ------------')
        print(classification_report(self.y_test, y_pred > t))
        print(confusion_matrix(self.y_test, y_pred > t))
        lgb.plot_importance(model)
        lgb.plot_importance(model, importance_type='gain')

        roc_display = RocCurveDisplay.from_predictions(
            self.y_test,
            y_pred,
            name="ROC - Test",
            color="darkblue",
            plot_chance_level=True,
        )

        roc_display = RocCurveDisplay.from_predictions(
            self.y_train,
            y_pred_train,
            name="ROC - Train",
            color="darkorange",
            plot_chance_level=False,
            ax=roc_display.ax_
        )

        _ = roc_display.ax_.set(
            xlabel="False Positive Rate",
            ylabel="True Positive Rate",
            title="ROC Curve",
        )

        plt.hist(y_pred, bins=15, alpha=0.5, label='Test', density=True)
        plt.hist(y_pred_train, bins=15, alpha=0.5, label='Train', density=True)
        plt.title('Density of test/train predictions')
        plt.legend()

        feature_importances = {f: imp for imp, f in
                               zip(model.feature_importances_, model.feature_name_)}
        dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

        # TODO: use log instead of print
        print(dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True)))
        plt.show()


def main() -> None:

    df_race_results_final = load_data('df_race_results_final')
    am = ArrivalModel(df_race_results_final, 'arrival_params.yaml')
    am.fit()
    am.plot()
    am.save_pickle(os.path.join(MODEL_PATH, 'arrival.pkl'))


if __name__ == '__main__':
    main()
