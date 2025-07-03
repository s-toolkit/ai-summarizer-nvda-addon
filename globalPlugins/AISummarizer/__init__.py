import addonHandler
import globalPluginHandler
import ui
import gui
import wx
import requests
import os
import json
import webbrowser
import socket
import threading
from urllib.parse import urlencode
import scriptHandler
import keyboardHandler
from logHandler import log

addonHandler.initTranslation()

# Supported file extensions and their MIME types for Google Gemini API
SUPPORTED_EXTENSIONS = {
    'mp4': 'video/mp4',
    'mkv': 'video/x-matroska',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'png': 'image/png',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'ico': 'image/x-icon',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pdf': 'application/pdf',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain',
    'py': 'text/x-python',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'java': 'text/x-java-source',
    'cpp': 'text/x-c++src',
    'c': 'text/x-csrc',
    'sh': 'application/x-sh'
}

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("AI Summarizer")

    def __init__(self):
        super().__init__()
        self._create_menu()
        self.bindGesture("kb:NVDA+Alt+N", "openAISummarizer")

    def _create_menu(self):
        """Create the menu for the AI Summarizer add-on."""
        try:
            self.tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
            self.ai_summarizer_menu = wx.Menu()
            self.ai_summarizer_item = self.ai_summarizer_menu.Append(
                wx.ID_ANY,
                _("AI Summarizer..."),
                _("Open AI Summarizer to summarize content")
            )
            self.about_item = self.ai_summarizer_menu.Append(
                wx.ID_ANY,
                _("About AI Summarizer..."),
                _("Information about AI Summarizer development")
            )
            self.menu = self.tools_menu.AppendSubMenu(
                self.ai_summarizer_menu,
                _("AI Summarizer"),
                _("AI Summarizer tools")
            )
            gui.mainFrame.sysTrayIcon.Bind(
                wx.EVT_MENU,
                self._on_ai_summarizer_menu,
                self.ai_summarizer_item
            )
            gui.mainFrame.sysTrayIcon.Bind(
                wx.EVT_MENU,
                self._on_about_menu,
                self.about_item
            )
        except Exception as e:
            log.error(f"Error creating menu: {e}")
            ui.message(_("Failed to create AI Summarizer menu"))

    def _on_ai_summarizer_menu(self, event):
        """Handle AI Summarizer menu item selection."""
        wx.CallAfter(self._show_main_dialog)

    def _on_about_menu(self, event):
        """Handle About menu item selection."""
        wx.CallAfter(self._show_about_dialog)

    def _show_main_dialog(self):
        """Show the main AI Summarizer dialog."""
        try:
            gui.mainFrame.prePopup()
            dialog = MainDialog(gui.mainFrame)
            dialog.Show()
        except Exception as e:
            log.error(f"Error showing main dialog: {e}")
            ui.message(_("Failed to open AI Summarizer dialog"))
        finally:
            gui.mainFrame.postPopup()

    def _show_about_dialog(self):
        """Show the About dialog."""
        try:
            gui.mainFrame.prePopup()
            dialog = AboutDialog(gui.mainFrame)
            dialog.Show()
        except Exception as e:
            log.error(f"Error showing about dialog: {e}")
            ui.message(_("Failed to open About dialog"))
        finally:
            gui.mainFrame.postPopup()

    def terminate(self):
        """Clean up when the add-on is unloaded."""
        try:
            self.tools_menu.Remove(self.menu)
        except (wx.PyDeadObjectError, AttributeError):
            pass

    @scriptHandler.script(
        description=_("Open the AI Summarizer dialog"),
        gesture="kb:NVDA+Alt+N"
    )
    def script_openAISummarizer(self, gesture):
        """Script to open the AI Summarizer dialog with NVDA+Alt+D."""
        wx.CallAfter(self._show_main_dialog)

class MainDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title=_("AI Summarizer"),
            size=(700, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.file_path = None
        self._setup_ui()
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_press)
        self.CentreOnScreen()

    def _setup_ui(self):
        """Set up the responsive UI for the main dialog."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Prompt section
        prompt_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Summarization Prompt")), wx.VERTICAL)
        self.prompt_label = wx.StaticText(self, label=_("How do you want the AI to describe your content?"))
        self.prompt_ctrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER,
            size=(600, 120)
        )
        self.prompt_ctrl.SetMinSize((600, 120))
        self.prompt_ctrl.SetFocus()
        prompt_sizer.Add(self.prompt_label, 0, wx.ALL, 5)
        prompt_sizer.Add(self.prompt_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(prompt_sizer, 1, wx.ALL | wx.EXPAND, 10)

        # File selection section
        file_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("File Selection")), wx.VERTICAL)
        self.attach_button = wx.Button(self, label=_("Attach a file (Alt+A)"))
        self.attach_button.Bind(wx.EVT_BUTTON, self._on_attach_file)
        file_sizer.Add(self.attach_button, 0, wx.ALL, 5)

        self.file_label = wx.StaticText(self, label=_("No file selected"))
        file_sizer.Add(self.file_label, 0, wx.ALL, 5)

        self.remove_button = wx.Button(self, label=_("Remove attached file (Alt+R)"))
        self.remove_button.Bind(wx.EVT_BUTTON, self._on_remove_file)
        self.remove_button.Disable()
        self.remove_button.Hide()
        file_sizer.Add(self.remove_button, 0, wx.ALL, 5)
        main_sizer.Add(file_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Buttons section
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.about_button = wx.Button(self, label=_("About (Alt+B)"))
        self.about_button.Bind(wx.EVT_BUTTON, self._on_about)
        button_sizer.Add(self.about_button, 0, wx.ALL, 5)

        self.summarize_button = wx.Button(self, label=_("Summarize (Alt+S)"))
        self.summarize_button.Bind(wx.EVT_BUTTON, self._on_summarize)
        button_sizer.Add(self.summarize_button, 0, wx.ALL, 5)

        self.close_button = wx.Button(self, label=_("Close (Alt+C)"))
        self.close_button.Bind(wx.EVT_BUTTON, self._on_close)
        button_sizer.Add(self.close_button, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self._bind_keyboard_shortcuts()

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts using wx.AcceleratorTable."""
        entries = [
            (wx.ACCEL_ALT, ord('A'), self.attach_button.GetId()),
            (wx.ACCEL_ALT, ord('R'), self.remove_button.GetId()),
            (wx.ACCEL_ALT, ord('B'), self.about_button.GetId()),
            (wx.ACCEL_ALT, ord('S'), self.summarize_button.GetId()),
            (wx.ACCEL_ALT, ord('C'), self.close_button.GetId())
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _on_attach_file(self, event):
        """Handle file attachment."""
        wildcard = "Supported files|" + ";".join(f"*.{ext}" for ext in SUPPORTED_EXTENSIONS)
        with wx.FileDialog(
            self,
            _("Select a file to summarize"),
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                self.file_path = file_dialog.GetPath()
                self.file_label.SetLabel(os.path.basename(self.file_path))
                self.remove_button.Enable()
                self.remove_button.Show()
                self.Layout()
                ui.message(_("File attached: {}").format(os.path.basename(self.file_path)))

    def _on_remove_file(self, event):
        """Handle file removal."""
        self.file_path = None
        self.file_label.SetLabel(_("No file selected"))
        self.remove_button.Disable()
        self.remove_button.Hide()
        self.Layout()
        ui.message(_("Attached file removed"))

    def _on_about(self, event):
        """Show About dialog."""
        AboutDialog(self).Show()

    def _on_summarize(self, event):
        """Initiate summarization process."""
        if not self.file_path:
            ui.message(_("Please attach a file to summarize"))
            return
        if not self.prompt_ctrl.GetValue().strip():
            ui.message(_("Please enter a prompt for summarization"))
            return
        if not self._check_internet_connection():
            gui.messageBox(
                _("No internet connection. Please check your network and try again."),
                _("Connection Error"),
                wx.OK | wx.ICON_ERROR
            )
            return
        self._process_summarization()

    def _check_internet_connection(self):
        """Check for internet connectivity."""
        try:
            socket.create_connection(("www.google.com", 80), timeout=5)
            return True
        except (socket.gaierror, socket.timeout):
            return False

    def _process_summarization(self):
        """Start the summarization process in a separate thread."""
        processing_dialog = ProcessingDialog(self)
        wx.CallAfter(processing_dialog.Show)
        threading.Thread(
            target=self._upload_and_summarize,
            args=(processing_dialog,),
            daemon=True
        ).start()

    def _upload_and_summarize(self, processing_dialog):
        """Upload file and generate summary using Google Gemini API."""
        try:
            file_ext = os.path.splitext(self.file_path)[1].lower().lstrip('.')
            if file_ext not in SUPPORTED_EXTENSIONS:
                wx.CallAfter(ui.message, _("Unsupported file format"))
                wx.CallAfter(processing_dialog.Destroy)
                return

            mime_type = SUPPORTED_EXTENSIONS[file_ext]
            with open(self.file_path, 'rb') as file:
                files = {'file': (os.path.basename(self.file_path), file, mime_type)}
                upload_url = "https://generativelanguage.googleapis.com/upload/v1beta/files?key=AIzaSyC2Fsjk3yCRA8hDVYgg5LlMn4sxwoJJaWU"
                response = requests.post(upload_url, files=files, timeout=30)
                response.raise_for_status()
                file_data = response.json()
                file_uri = file_data.get('file', {}).get('uri')

            if not file_uri:
                wx.CallAfter(ui.message, _("Failed to upload file"))
                wx.CallAfter(processing_dialog.Destroy)
                return

            prompt = self.prompt_ctrl.GetValue()
            summary_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=AIzaSyC2Fsjk3yCRA8hDVYgg5LlMn4sxwoJJaWU"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {"fileData": {"fileUri": file_uri, "mimeType": mime_type}}
                        ]
                    }
                ]
            }
            headers = {'Content-Type': 'application/json'}
            summary_response = requests.post(
                summary_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            summary_text = summary_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

            wx.CallAfter(processing_dialog.Destroy)
            wx.CallAfter(self._show_response_dialog, summary_text)

        except requests.exceptions.RequestException as e:
            wx.CallAfter(ui.message, _("Network error: {}").format(str(e)))
            wx.CallAfter(processing_dialog.Destroy)
        except Exception as e:
            wx.CallAfter(ui.message, _("Error occurred: {}").format(str(e)))
            wx.CallAfter(processing_dialog.Destroy)

    def _show_response_dialog(self, summary_text):
        """Show the response dialog with the summary."""
        response_dialog = ResponseDialog(self, summary_text, self.file_path, self.prompt_ctrl.GetValue())
        wx.CallAfter(response_dialog.Show)

    def _on_close(self, event):
        """Close the dialog."""
        self.Destroy()

    def _on_key_press(self, event):
        """Handle key press events."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._on_close(event)
        else:
            event.Skip()

class ProcessingDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title=_("Summarizing..."),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        )
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddStretchSpacer()
        sizer.Add(wx.StaticText(self, label=_("Please wait, AI is summarizing your content...")), 0, wx.ALL | wx.ALIGN_CENTER, 10)
        sizer.AddStretchSpacer()
        self.SetSizer(sizer)
        self.Fit()
        self.CentreOnParent()

class ResponseDialog(wx.Dialog):
    def __init__(self, parent, summary_text, file_path, prompt):
        super().__init__(
            parent,
            title=_("AI Summarizer - Response"),
            size=(700, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.summary_text = summary_text
        self.file_path = file_path
        self.prompt = prompt
        self._setup_ui()
        self.Bind(wx.EVT_CHAR_HOOK, self._on_key_press)
        self.CentreOnScreen()

    def _setup_ui(self):
        """Set up the responsive UI for the response dialog."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        output_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Summary Output")), wx.VERTICAL)
        self.output_label = wx.StaticText(self, label=_("Summary"))
        self.output_ctrl = wx.TextCtrl(
            self,
            value=self.summary_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH,
            size=(600, 250)
        )
        self.output_ctrl.SetMinSize((600, 250))
        output_sizer.Add(self.output_label, 0, wx.ALL, 5)
        output_sizer.Add(self.output_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(output_sizer, 1, wx.ALL | wx.EXPAND, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.copy_button = wx.Button(self, label=_("Copy (Alt+C)"))
        self.copy_button.Bind(wx.EVT_BUTTON, self._on_copy)
        button_sizer.Add(self.copy_button, 0, wx.ALL, 5)

        self.export_button = wx.Button(self, label=_("Export Summary (Alt+E)"))
        self.export_button.Bind(wx.EVT_BUTTON, self._on_export)
        button_sizer.Add(self.export_button, 0, wx.ALL, 5)

        self.regenerate_button = wx.Button(self, label=_("Regenerate Summary (Alt+R)"))
        self.regenerate_button.Bind(wx.EVT_BUTTON, self._on_regenerate)
        button_sizer.Add(self.regenerate_button, 0, wx.ALL, 5)

        self.back_button = wx.Button(self, label=_("Back (Alt+B)"))
        self.back_button.Bind(wx.EVT_BUTTON, self._on_back)
        button_sizer.Add(self.back_button, 0, wx.ALL, 5)

        self.close_button = wx.Button(self, label=_("Close (Alt+L)"))
        self.close_button.Bind(wx.EVT_BUTTON, self._on_close)
        button_sizer.Add(self.close_button, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        self._bind_keyboard_shortcuts()

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts using wx.AcceleratorTable."""
        entries = [
            (wx.ACCEL_ALT, ord('C'), self.copy_button.GetId()),
            (wx.ACCEL_ALT, ord('E'), self.export_button.GetId()),
            (wx.ACCEL_ALT, ord('R'), self.regenerate_button.GetId()),
            (wx.ACCEL_ALT, ord('B'), self.back_button.GetId()),
            (wx.ACCEL_ALT, ord('L'), self.close_button.GetId())
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _on_copy(self, event):
        """Copy summary to clipboard."""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.summary_text))
            wx.TheClipboard.Close()
            ui.message(_("Copied to clipboard"))

    def _on_export(self, event):
        """Export summary to a file."""
        with wx.FileDialog(
            self,
            _("Save summary as"),
            defaultFile="summary.txt",
            wildcard="Text files (*.txt)|*.txt",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                path = file_dialog.GetPath()
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(self.summary_text)
                    ui.message(_("Summary exported to {}").format(path))
                except Exception as e:
                    ui.message(_("Error exporting summary: {}").format(str(e)))

    def _on_regenerate(self, event):
        """Regenerate the summary."""
        self.Destroy()
        main_dialog = self.GetParent()
        wx.CallAfter(main_dialog._process_summarization)

    def _on_back(self, event):
        """Return to the main dialog."""
        self.Destroy()
        main_dialog = self.GetParent()
        wx.CallAfter(main_dialog.Show)

    def _on_close(self, event):
        """Close the dialog."""
        self.Destroy()

    def _on_key_press(self, event):
        """Handle key press events."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._on_close(event)
        elif event.GetKeyCode() == wx.WXK_BACK:
            self._on_back(event)
        else:
            event.Skip()

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title=_("About AI Summarizer"),
            size=(450, 350),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self._setup_ui()
        self.CentreOnParent()

    def _setup_ui(self):
        """Set up the UI for the About dialog."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        message = _(
            "AI Summarizer: Developed by Sujan Rai at Team of Tech Visionary. Version 2.3\n"
            "This add-on enables summarization of code, audio, video, document or image files using AI.\n"
            "Subscribe to our YouTube channel for the latest technical tutorials for Windows and Android."
        )
        label = wx.StaticText(self, label=message)
        label.Wrap(400)
        main_sizer.Add(label, 0, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.subscribe_button = wx.Button(self, label=_("Subscribe to YouTube Channel (Alt+S)"))
        self.subscribe_button.Bind(wx.EVT_BUTTON, self._on_subscribe)
        button_sizer.Add(self.subscribe_button, 0, wx.ALL, 5)

        self.close_button = wx.Button(self, label=_("Close (Alt+C)"))
        self.close_button.Bind(wx.EVT_BUTTON, self._on_close)
        button_sizer.Add(self.close_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        self.SetSizer(main_sizer)
        self.Fit()
        self._bind_keyboard_shortcuts()

    def _bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts using wx.AcceleratorTable."""
        entries = [
            (wx.ACCEL_ALT, ord('S'), self.subscribe_button.GetId()),
            (wx.ACCEL_ALT, ord('C'), self.close_button.GetId())
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _on_subscribe(self, event):
        """Open YouTube channel in browser."""
        webbrowser.open("https://youtube.com/@blindtechvisionary")
        self.Destroy()

    def _on_close(self, event):
        """Close the dialog."""
        self.Destroy()
