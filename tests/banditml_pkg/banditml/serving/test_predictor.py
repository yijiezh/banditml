from copy import deepcopy
import json
import os
import unittest

import numpy as np

from banditml_pkg.banditml import model_io
from banditml_pkg.banditml.preprocessing import preprocessor
from banditml_pkg.banditml.serving.predictor import BanditPredictor
from sklearn.utils import shuffle
from tests.fixtures import Params, Datasets
from workflows import train_bandit


TMP_MODEL_PATH = os.path.dirname(os.path.abspath(__file__)) + "/tmp.pkl"


class TestPredictor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tol = 0.001
        cls.tmp_model_path = TMP_MODEL_PATH
        cls.shared_params = deepcopy(Params.SHARED_PARAMS)
        cls.shared_params["max_epochs"] = 10

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.tmp_model_path)

    def test_same_predictions_country_as_categorical(self):
        raw_data = shuffle(Datasets._raw_data)
        rand_idx = 0
        test_input = raw_data.iloc[rand_idx]

        data = preprocessor.preprocess_data(
            raw_data,
            Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_CATEGORICAL,
            shuffle_data=False,  # don't shuffle so we can test the same observation
        )

        _X, _y = preprocessor.data_to_pytorch(data)

        X_COUNTRY_CATEG = {
            "X_train": {"X_float": _X["X_float"][: Datasets._offset]},
            "y_train": _y[: Datasets._offset],
            "X_test": {"X_float": _X["X_float"][Datasets._offset :]},
            "y_test": _y[Datasets._offset :],
        }

        pytorch_net = train_bandit.build_pytorch_net(
            feature_specs=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_CATEGORICAL[
                "features"
            ],
            product_sets=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_CATEGORICAL[
                "product_sets"
            ],
            float_feature_order=Datasets.DATA_COUNTRY_CATEG[
                "final_float_feature_order"
            ],
            id_feature_order=Datasets.DATA_COUNTRY_CATEG["final_id_feature_order"],
            layers=self.shared_params["model"]["layers"],
            activations=self.shared_params["model"]["activations"],
            input_dim=train_bandit.num_float_dim(Datasets.DATA_COUNTRY_CATEG),
        )

        skorch_net = train_bandit.fit_custom_pytorch_module_w_skorch(
            module=pytorch_net,
            X=X_COUNTRY_CATEG["X_train"],
            y=X_COUNTRY_CATEG["y_train"],
            hyperparams=self.shared_params,
        )

        pre_pickle_predictor = BanditPredictor(
            experiment_specific_params=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_CATEGORICAL,
            float_feature_order=Datasets.DATA_COUNTRY_CATEG["float_feature_order"],
            id_feature_order=Datasets.DATA_COUNTRY_CATEG["id_feature_order"],
            transforms=Datasets.DATA_COUNTRY_CATEG["transforms"],
            imputers=Datasets.DATA_COUNTRY_CATEG["imputers"],
            net=skorch_net,
        )

        model_io.write_predictor_to_disk(pre_pickle_predictor, self.tmp_model_path)
        post_pickle_predictor = model_io.read_predictor_from_disk(self.tmp_model_path)

        pre_pred = skorch_net.predict(X_COUNTRY_CATEG["X_train"])[rand_idx]
        post_pred = post_pickle_predictor.predict(json.loads(test_input.context))

        assert np.isclose(
            pre_pred, post_pred["scores"][test_input.decision - 1], self.tol
        )

    def test_same_predictions_country_as_id_list(self):
        raw_data = shuffle(Datasets._raw_data)
        rand_idx = 0
        test_input = raw_data.iloc[rand_idx]

        data = preprocessor.preprocess_data(
            raw_data,
            Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_ID_LIST,
            shuffle_data=False,  # don't shuffle so we can test the same observation
        )

        _X, _y = preprocessor.data_to_pytorch(data)
        X_COUNTRY_ID_LIST = {
            "X_train": {
                "X_float": _X["X_float"][: Datasets._offset],
                "X_id_list": _X["X_id_list"][: Datasets._offset],
                "X_id_list_idxs": _X["X_id_list_idxs"][: Datasets._offset],
            },
            "y_train": _y[: Datasets._offset],
            "X_test": {
                "X_float": _X["X_float"][Datasets._offset :],
                "X_id_list": _X["X_id_list"][Datasets._offset :],
                "X_id_list_idxs": _X["X_id_list_idxs"][Datasets._offset :],
            },
            "y_test": _y[Datasets._offset :],
        }

        pytorch_net = train_bandit.build_pytorch_net(
            feature_specs=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_ID_LIST[
                "features"
            ],
            product_sets=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_ID_LIST[
                "product_sets"
            ],
            float_feature_order=Datasets.DATA_COUNTRY_ID_LIST[
                "final_float_feature_order"
            ],
            id_feature_order=Datasets.DATA_COUNTRY_ID_LIST["final_id_feature_order"],
            layers=self.shared_params["model"]["layers"],
            activations=self.shared_params["model"]["activations"],
            input_dim=train_bandit.num_float_dim(Datasets.DATA_COUNTRY_ID_LIST),
        )

        skorch_net = train_bandit.fit_custom_pytorch_module_w_skorch(
            module=pytorch_net,
            X=X_COUNTRY_ID_LIST["X_train"],
            y=X_COUNTRY_ID_LIST["y_train"],
            hyperparams=self.shared_params,
        )

        pre_pickle_predictor = BanditPredictor(
            experiment_specific_params=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_ID_LIST,
            float_feature_order=Datasets.DATA_COUNTRY_ID_LIST["float_feature_order"],
            id_feature_order=Datasets.DATA_COUNTRY_ID_LIST["id_feature_order"],
            transforms=Datasets.DATA_COUNTRY_ID_LIST["transforms"],
            imputers=Datasets.DATA_COUNTRY_ID_LIST["imputers"],
            net=skorch_net,
        )

        model_io.write_predictor_to_disk(pre_pickle_predictor, self.tmp_model_path)
        post_pickle_predictor = model_io.read_predictor_from_disk(self.tmp_model_path)

        pre_pred = skorch_net.predict(X_COUNTRY_ID_LIST["X_train"])[rand_idx]
        post_pred = post_pickle_predictor.predict(json.loads(test_input.context))

        assert np.isclose(
            pre_pred, post_pred["scores"][test_input.decision - 1], self.tol
        )

    def test_same_predictions_country_as_dense_id_list(self):
        raw_data = shuffle(Datasets._raw_data)
        rand_idx = 0
        test_input = raw_data.iloc[rand_idx]

        data = preprocessor.preprocess_data(
            raw_data,
            Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_DENSE_ID_LIST,
            shuffle_data=False,  # don't shuffle so we can test the same observation
        )

        _X, _y = preprocessor.data_to_pytorch(data)
        X_COUNTRY_DENSE_ID_LIST = {
            "X_train": {"X_float": _X["X_float"][: Datasets._offset]},
            "y_train": _y[: Datasets._offset],
            "X_test": {"X_float": _X["X_float"][Datasets._offset :]},
            "y_test": _y[Datasets._offset :],
        }

        pytorch_net = train_bandit.build_pytorch_net(
            feature_specs=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_DENSE_ID_LIST[
                "features"
            ],
            product_sets=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_DENSE_ID_LIST[
                "product_sets"
            ],
            float_feature_order=Datasets.DATA_COUNTRY_DENSE_ID_LIST[
                "final_float_feature_order"
            ],
            id_feature_order=Datasets.DATA_COUNTRY_DENSE_ID_LIST[
                "final_id_feature_order"
            ],
            layers=self.shared_params["model"]["layers"],
            activations=self.shared_params["model"]["activations"],
            input_dim=train_bandit.num_float_dim(Datasets.DATA_COUNTRY_DENSE_ID_LIST),
        )

        skorch_net = train_bandit.fit_custom_pytorch_module_w_skorch(
            module=pytorch_net,
            X=X_COUNTRY_DENSE_ID_LIST["X_train"],
            y=X_COUNTRY_DENSE_ID_LIST["y_train"],
            hyperparams=self.shared_params,
        )

        pre_pickle_predictor = BanditPredictor(
            experiment_specific_params=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AS_DENSE_ID_LIST,
            float_feature_order=Datasets.DATA_COUNTRY_DENSE_ID_LIST[
                "float_feature_order"
            ],
            id_feature_order=Datasets.DATA_COUNTRY_DENSE_ID_LIST["id_feature_order"],
            transforms=Datasets.DATA_COUNTRY_DENSE_ID_LIST["transforms"],
            imputers=Datasets.DATA_COUNTRY_DENSE_ID_LIST["imputers"],
            net=skorch_net,
        )

        model_io.write_predictor_to_disk(pre_pickle_predictor, self.tmp_model_path)
        post_pickle_predictor = model_io.read_predictor_from_disk(self.tmp_model_path)

        pre_pred = skorch_net.predict(X_COUNTRY_DENSE_ID_LIST["X_train"])[rand_idx]
        post_pred = post_pickle_predictor.predict(json.loads(test_input.context))

        assert np.isclose(
            pre_pred, post_pred["scores"][test_input.decision - 1], self.tol
        )

    def test_same_predictions_country_and_decision_as_id_list(self):
        raw_data = shuffle(Datasets._raw_data)
        rand_idx = 0
        test_input = raw_data.iloc[rand_idx]

        data = preprocessor.preprocess_data(
            raw_data,
            Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AND_DECISION_AS_ID_LIST,
            shuffle_data=False,  # don't shuffle so we can test the same observation
        )

        _X, _y = preprocessor.data_to_pytorch(data)
        X_COUNTRY_AND_DECISION_ID_LIST = {
            "X_train": {
                "X_float": _X["X_float"][: Datasets._offset],
                "X_id_list": _X["X_id_list"][: Datasets._offset],
                "X_id_list_idxs": _X["X_id_list_idxs"][: Datasets._offset],
            },
            "y_train": _y[: Datasets._offset],
            "X_test": {
                "X_float": _X["X_float"][Datasets._offset :],
                "X_id_list": _X["X_id_list"][Datasets._offset :],
                "X_id_list_idxs": _X["X_id_list_idxs"][Datasets._offset :],
            },
            "y_test": _y[Datasets._offset :],
        }

        pytorch_net = train_bandit.build_pytorch_net(
            feature_specs=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AND_DECISION_AS_ID_LIST[
                "features"
            ],
            product_sets=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AND_DECISION_AS_ID_LIST[
                "product_sets"
            ],
            float_feature_order=Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST[
                "final_float_feature_order"
            ],
            id_feature_order=Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST[
                "final_id_feature_order"
            ],
            layers=self.shared_params["model"]["layers"],
            activations=self.shared_params["model"]["activations"],
            input_dim=train_bandit.num_float_dim(
                Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST
            ),
        )

        skorch_net = train_bandit.fit_custom_pytorch_module_w_skorch(
            module=pytorch_net,
            X=X_COUNTRY_AND_DECISION_ID_LIST["X_train"],
            y=X_COUNTRY_AND_DECISION_ID_LIST["y_train"],
            hyperparams=self.shared_params,
        )

        pre_pickle_predictor = BanditPredictor(
            experiment_specific_params=Params.EXPERIMENT_SPECIFIC_PARAMS_COUNTRY_AND_DECISION_AS_ID_LIST,
            float_feature_order=Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST[
                "float_feature_order"
            ],
            id_feature_order=Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST[
                "id_feature_order"
            ],
            transforms=Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST["transforms"],
            imputers=Datasets.DATA_COUNTRY_AND_DECISION_ID_LIST["imputers"],
            net=skorch_net,
        )

        model_io.write_predictor_to_disk(pre_pickle_predictor, self.tmp_model_path)
        post_pickle_predictor = model_io.read_predictor_from_disk(self.tmp_model_path)

        pre_pred = skorch_net.predict(X_COUNTRY_AND_DECISION_ID_LIST["X_train"])[
            rand_idx
        ]
        post_pred = post_pickle_predictor.predict(json.loads(test_input.context))

        assert np.isclose(
            pre_pred, post_pred["scores"][test_input.decision - 1], self.tol
        )
