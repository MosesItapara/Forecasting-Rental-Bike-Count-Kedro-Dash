from kedro.pipeline import Pipeline, node
from .nodes import make_target, split_data, train_model, predict, compute_metrics, save_model


def create_training_pipeline() -> Pipeline:
    return Pipeline([
        node(
            func=make_target,
            inputs=["features", "params:training.target_params"],
            outputs="data_with_target",
        ),
        node(
            func=split_data,
            inputs=["data_with_target", "params:training"],
            outputs=["x_train", "x_test", "y_train", "y_test"],
        ),
        node(
            func=train_model,
            inputs=["x_train", "y_train", "params:training"],
            outputs="trained_model",
        ),
        node(
            func=predict,
            inputs=["trained_model", "x_test"],
            outputs="predictions",
        ),
        node(
            func=compute_metrics,
            inputs=["y_test", "predictions"],
            outputs="metrics",
        ),
        node(
            func=save_model,
            inputs=["trained_model", "params:training.model_type", "params:model_storage"],
            outputs=None,
        )

    ])