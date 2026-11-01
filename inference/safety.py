"""Rule-based temperature safety class, kept separate from the model (never counted in model metrics).
|mean - 4 C| > 1 -> Warning (1); > 3 -> Critical (2), matching the brief's class definitions."""


def safety_class(temp_mean, setpoint=4.0):
    d = abs(float(temp_mean) - setpoint)
    return 2 if d > 3 else 1 if d > 1 else 0
