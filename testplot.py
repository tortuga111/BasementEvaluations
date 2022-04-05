import plotly.graph_objects as go

if __name__ == "__main__":
    x = [1]
    y = [1]
    text = "anzeige"

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=x,
            y=x,
            mode="markers",
            name="test",
            hovertemplate=text,
        )
    )
    figure.update_layout(
        xaxis=dict(title="test"),
        yaxis=dict(title="test y"),
    )

    figure.show()
