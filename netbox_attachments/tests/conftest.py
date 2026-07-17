"""Shared fakes for the standalone pytest suite."""

from types import SimpleNamespace


def fake_model(app_label: str, model_name: str):
    """
    A stand-in model class whose _meta mirrors every attribute production code reads.

    One definition on purpose: when the code under test starts reading a new _meta
    attribute (as label_lower was added in #111), it is added here once instead of
    being chased through per-file copies. Call it for a class, call the result for
    an instance: fake_model("dcim", "device")().
    """
    return type(
        "FakeModel",
        (),
        {
            "_meta": SimpleNamespace(
                app_label=app_label,
                model_name=model_name,
                label_lower=f"{app_label}.{model_name}",
                abstract=False,
            )
        },
    )
