from datetime import datetime
from pathlib import Path

from nicegui import events, ui

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@ui.page("/")
def index() -> None:
    messages: list[dict] = []
    pending_files: list[dict] = []  # {name, path}

    with ui.column().classes("w-full max-w-3xl mx-auto h-screen p-4 gap-2"):
        ui.label("Chat").classes("text-2xl font-bold")

        with ui.scroll_area().classes(
            "w-full flex-grow bg-white rounded shadow p-2"
        ) as chat_area:
            chat_box = ui.column().classes("w-full gap-2")

        attachments_row = ui.row().classes("gap-1 flex-wrap")

        def render_messages() -> None:
            chat_box.clear()
            with chat_box:
                for m in messages:
                    ui.chat_message(
                        text=m["text"] or " ",
                        name="You" if m["role"] == "user" else "Bot",
                        stamp=m["stamp"],
                        sent=m["role"] == "user",
                    )
                    if m["files"]:
                        align = "justify-end" if m["role"] == "user" else "justify-start"
                        with ui.row().classes(f"w-full {align} gap-1 flex-wrap -mt-2"):
                            for f in m["files"]:
                                ui.chip(f, icon="attach_file").props("dense outline")
            chat_area.scroll_to(percent=1.0)

        def render_attachments() -> None:
            attachments_row.clear()
            with attachments_row:
                for f in pending_files:
                    with ui.chip(f["name"], icon="attach_file").props("dense removable") as chip:
                        chip.on(
                            "remove",
                            lambda _, name=f["name"]: remove_pending(name),
                        )

        def remove_pending(name: str) -> None:
            for f in list(pending_files):
                if f["name"] == name:
                    pending_files.remove(f)
                    Path(f["path"]).unlink(missing_ok=True)
            render_attachments()

        def handle_upload(e: events.UploadEventArguments) -> None:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            dest = UPLOAD_DIR / f"{stamp}-{e.name}"
            dest.write_bytes(e.content.read())
            pending_files.append({"name": e.name, "path": str(dest)})
            render_attachments()

        def send() -> None:
            text = text_input.value.strip()
            if not text and not pending_files:
                return
            messages.append(
                {
                    "role": "user",
                    "text": text,
                    "files": [f["name"] for f in pending_files],
                    "stamp": datetime.now().strftime("%H:%M"),
                }
            )
            attached_count = len(pending_files)
            text_input.value = ""
            pending_files.clear()
            render_attachments()
            uploader.reset()
            reply = "Got it."
            if attached_count:
                reply = f"Got it — received {attached_count} file(s)."
            messages.append(
                {
                    "role": "assistant",
                    "text": reply,
                    "files": [],
                    "stamp": datetime.now().strftime("%H:%M"),
                }
            )
            render_messages()

        with ui.row().classes("w-full items-end gap-2"):
            uploader = (
                ui.upload(
                    on_upload=handle_upload,
                    multiple=True,
                    auto_upload=True,
                )
                .props("flat dense hide-upload-btn accept=*")
                .classes("max-w-xs")
            )
            text_input = (
                ui.input(placeholder="Type a message...")
                .props("outlined dense")
                .classes("flex-grow")
                .on("keydown.enter", send)
            )
            ui.button(icon="send", on_click=send).props("round color=primary")

        render_messages()


ui.run(title="Chat", port=8080, reload=False, show=False)