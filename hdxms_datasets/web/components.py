import solara
from hdxms_datasets.web.state import snackbar


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
