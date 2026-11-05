import asyncio

import shadlet as ui

app = ui.App("Background task")


@app.page("/")
def home(ctx: ui.Context) -> ui.Component:
    task_state = ctx.task_state("report", label="Report")

    async def generate_report(task: ui.BackgroundTask) -> None:
        for step in range(1, 6):
            await asyncio.sleep(0.5)
            await task.update(
                progress=step * 20,
                message=f"Preparing section {step} of 5",
            )

    def start_report(event: ui.ClickEvent) -> None:
        if task_state.value["status"] != "running":
            ctx.start_task("Generate report", generate_report, key="report")

    status = task_state.value
    return ui.Center(
        ui.Column(
            ui.Heading("Report generation", level=1),
            ui.Text(status["message"] or "Ready to generate a report."),
            ui.Progress(value=status["progress"]),
            ui.Text(f"Status: {status['status']}"),
            ui.Button(
                "Generate report",
                on_click=start_report,
                disabled=status["status"] == "running",
            ),
            gap=16,
            max_width=520,
            padding=24,
        ),
        min_height="100vh",
        padding=24,
    )


if __name__ == "__main__":
    app.run()
