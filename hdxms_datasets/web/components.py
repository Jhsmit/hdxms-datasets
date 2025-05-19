from typing import Callable, Optional, Union
import solara
from hdxms_datasets.web.state import snackbar
from solara.components.input import _InputNumeric


@solara.component
def Snackbar():
    snackbar_message = snackbar.value
    close_btn = solara.Button(
        label="close",
        color=snackbar_message.btn_color,
        text=True,
        on_click=lambda: snackbar.update(show=False),
    )
    children = [snackbar_message.message, close_btn]
    solara.v.Snackbar(
        v_model=snackbar_message.show,
        color=snackbar_message.color,
        timeout=snackbar_message.timeout,
        on_v_model=lambda x: snackbar.update(show=x),
        children=children,
    )


def td(*args):
    return solara.v.Html(tag="td", children=list(args))


def th(title: str):
    return solara.v.Html(tag="th", children=[title])


def tr():
    return solara.v.Html(tag="tr")


def h2(title: str):
    return solara.v.Html(tag="h2", children=[title])


def strong(content: str):
    return solara.v.Html(tag="strong", children=[content])


num = float | int


@solara.component
def InputNumeric(
    label: str,
    value: Union[None, num, solara.Reactive[num], solara.Reactive[Optional[num]]] = 0,
    on_value: Union[None, Callable[[Optional[num]], None], Callable[[num], None]] = None,
    disabled: bool = False,
    optional: bool = False,
    continuous_update: bool = False,
    clearable: bool = False,
    classes: list[str] = [],
    style: Optional[Union[str, dict[str, str]]] = None,
    autofocus: bool = False,
):
    """Numeric input (float | integers).

    Basic example:

    ```solara
    import solara

    int_value = solara.reactive(42)
    continuous_update = solara.reactive(True)

    @solara.component
    def Page():
        solara.Checkbox(label="Continuous update", value=continuous_update)
        solara.InputInt("Enter an integer number", value=int_value, continuous_update=continuous_update.value)
        with solara.Row():
            solara.Button("Clear", on_click=lambda: int_value.set(42))
        solara.Markdown(f"**You entered**: {int_value.value}")
    ```

    ## Arguments

    * `label`: Label to display next to the slider.
    * `value`: The currently entered value.
    * `on_value`: Callback to call when the value changes.
    * `disabled`: Whether the input is disabled.
    * `optional`: Whether the value can be None.
    * `continuous_update`: Whether to call the `on_value` callback on every change or only when the input loses focus or the enter key is pressed.
    * `clearable`: Whether the input can be cleared.
    * `classes`: List of CSS classes to apply to the input.
    * `style`: CSS style to apply to the input.
    * `autofocus`: Determines if a component is to be autofocused or not (Default is False). Autofocus will occur either during page load, or when the component becomes visible (for example, dialog being opened). Only one component per page should have autofocus on each such event.
    """

    def str_to_num(value: Optional[str]):
        if value:
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    raise ValueError(f"Cannot convert {value} to a number")
        else:
            if optional:
                return None
            else:
                raise ValueError("Value cannot be empty")

    return _InputNumeric(
        str_to_num,
        label=label,
        value=value,
        on_value=on_value,
        disabled=disabled,
        continuous_update=continuous_update,
        clearable=clearable,
        classes=classes,
        style=style,
        autofocus=autofocus,
    )
