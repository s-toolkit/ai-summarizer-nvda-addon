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
import keyboardHandler
import scriptHandler
from logHandler import log
import config

addonHandler.initTranslation()

# Constants
API_KEY = 'AIzaSyC2Fsjk3yCRA8hDVYgg5LlMn4sxwoJJaWU'
UPLOAD_URL = "https://generativelanguage.googleapis.com/upload/v1beta/files"
SUMMARY_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
YOUTUBE_CHANNEL_URL = "https://youtube.com/@blindtechvisionary"

# Supported file extensions and their MIME types
SUPPORTED_EXTENSIONS = {
    'py': 'text/x-python',
    'ts': 'application/typescript',
    'php': 'application/x-php',
    'html': 'text/html',
    'css': 'text/css',
    'js': 'application/javascript',
    'java': 'text/x-java-source',
    'cpp': 'text/x-c++src',
    'c': 'text/x-csrc',
    'cs': 'text/x-csharp',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'png': 'image/png',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'ico': 'image/x-icon',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'pdf': 'application/pdf',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain'
}

# File type limits
FILE_LIMITS = {
    'audio': {
        'extensions': ['mp3', 'wav'],
        'max_size': 300 * 1024 * 1024  # 300MB
    },
    'video': {
        'extensions': ['mp4', 'webm'],
        'max_size': 300 * 1024 * 1024  # 300MB
    },
    'image': {
        'extensions': ['png', 'jpeg', 'jpg', 'ico'],
        'max_size': 10 * 1024 * 1024  # 10MB
    },
    'document': {
        'extensions': ['docx', 'pdf', 'xlsx', 'txt'],
        'max_size': 50 * 1024 * 1024  # 50MB
    }
}

def get_file_type(file_ext):
    """Determine the file type based on extension."""
    for file_type, info in FILE_LIMITS.items():
        if file_ext in info['extensions']:
            return file_type
    return 'document'

def validate_file(file_path):
    """Validate file based on type and size limits."""
    if not os.path.exists(file_path):
        ui.message(_("File does not exist"))
        return False

    file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if file_ext not in SUPPORTED_EXTENSIONS:
        ui.message(_("Unsupported file format: {}").format(file_ext))
        return False

    file_size = os.path.getsize(file_path)
    file_type = get_file_type(file_ext)

    if file_size > FILE_LIMITS[file_type]['max_size']:
        ui.message(_(
            f"{file_type.capitalize()} file exceeds {FILE_LIMITS[file_type]['max_size'] // (1024 * 1024)}MB limit"
        ))
        return False

    return True

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = _("AI Summarizer")

    def __init__(self):
        super().__init__()
        self.menu = None
        self._create_menu()

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
            gui.mainFrame.postPopup()
        except Exception as e:
            log.error(f"Error showing main dialog: {e}")
            ui.message(_("Failed to open AI Summarizer dialog"))
            gui.mainFrame.postPopup()

    def _show_about_dialog(self):
        """Show the About dialog."""
        try:
            gui.mainFrame.prePopup()
            dialog = AboutDialog(gui.mainFrame)
            dialog.Show()
            gui.mainFrame.postPopup()
        except Exception as e:
            log.error(f"Error showing about dialog: {e}")
            ui.message(_("Failed to open About dialog"))
            gui.mainFrame.postPopup()

    def terminate(self):
        """Clean up when the add-on is unloaded."""
        try:
            if self.menu:
                self.tools_menu.Remove(self.menu)
        except Exception:
            pass

    @scriptHandler.script(
        description=_("Open the AI Summarizer dialog"),
        gesture="kb:NVDA+Alt+N"
    )
    def script_openAISummarizer(self, gesture):
        """Script to open the AI Summarizer dialog with NVDA+Alt+N."""
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
        self.Bind(wx.EVT_CHAR_HOOK, self._handle_key_press)
        self.CentreOnScreen()

    def _setup_ui(self):
        """Set up the responsive UI for the main dialog."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Prompt section
        prompt_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Summarization Prompt")), wx.VERTICAL)
        self.prompt_label = wx.StaticText(self, label=_("How do you want the AI to summarize your content?"))
        self.prompt_label.SetName("SummarizationPromptLabel")
        self.prompt_ctrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER,
            size=(600, 120),
            name="SummarizationPrompt"
        )
        self.prompt_ctrl.SetMinSize((600, 120))
        self.prompt_ctrl.SetFocus()
        prompt_sizer.Add(self.prompt_label, 0, wx.ALL, 5)
        prompt_sizer.Add(self.prompt_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(prompt_sizer, 1, wx.ALL | wx.EXPAND, 10)

        # File selection section
        file_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("File Selection")), wx.VERTICAL)
        self.attach_button = wx.Button(self, label=_("Attach a file (Alt+A)"), name="AttachFileButton")
        self.attach_button.Bind(wx.EVT_BUTTON, self._on_attach_file)
        file_sizer.Add(self.attach_button, 0, wx.ALL, 5)

        self.file_label = wx.StaticText(self, label=_("No file selected"), name="SelectedFileLabel")
        file_sizer.Add(self.file_label, 0, wx.ALL, 5)

        self.remove_button = wx.Button(self, label=_("Remove attached file (Alt+R)"), name="RemoveFileButton")
        self.remove_button.Bind(wx.EVT_BUTTON, self._on_remove_file)
        self.remove_button.Disable()
        file_sizer.Add(self.remove_button, 0, wx.ALL, 5)
        main_sizer.Add(file_sizer, 0, wx.ALL | wx.EXPAND, 10)

        # Buttons section
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.about_button = wx.Button(self, label=_("About (Alt+B)"), name="AboutButton")
        self.about_button.Bind(wx.EVT_BUTTON, self._on_about)
        button_sizer.Add(self.about_button, 0, wx.ALL, 5)

        self.summarize_button = wx.Button(self, label=_("Summarize (Alt+S)"), name="Summ SummarizeButton")
        self.summarize_button.Bind(wx.EVT_BUTTON, self._on_summarize)
        button_sizer.Add(self.summarize_button, 0, wx.ALL, 5)

        self.close_button = wx.Button(self, label=_("Close (Alt+C)"), name="CloseButton")
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
        """Handle file attachment with validation."""
        wildcard = "Supported files|" + ";".join(f"*.{ext}" for ext in SUPPORTED_EXTENSIONS)
        with wx.FileDialog(
            self,
            _("Select a file to summarize"),
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as file_dialog:
            if file_dialog.ShowModal() == wx.ID_OK:
                self.file_path = file_dialog.GetPath()
                if validate_file(self.file_path):
                    self.file_label.SetLabel(os.path.basename(self.file_path))
                    self.remove_button.Enable()
                    self.Layout()
                    ui.message(_("File attached: {}").format(os.path.basename(self.file_path)))
                else:
                    self.file_path = None
                    self.file_label.SetLabel(_("No file selected"))

    def _on_remove_file(self, event):
        """Handle file removal."""
        self.file_path = None
        self.file_label.SetLabel(_("No file selected"))
        self.remove_button.Disable()
        self.Layout()
        ui.message(_("Attached file removed"))

    def _on_about(self, event):
        """Show About dialog."""
        wx.CallAfter(self._show_about_dialog)

    def _show_about_dialog(self):
        """Show the About dialog."""
        try:
            dialog = AboutDialog(self)
            dialog.ShowModal()
            dialog.Destroy()
        except Exception as e:
            log.error(f"Error showing about dialog: {e}")
            ui.message(_("Failed to open About dialog"))

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
        except (socket.gaierror, socket.timeout, OSError):
            return False

    def _process_summarization(self):
        """Start the summarization process in a separate thread."""
        processing_dialog = ProcessingDialog(self)
        wx.CallAfter(processing_dialog.Show)
        threading.Thread(
            target=self._upload_and_summarize,
            args=(processing_dialog, self.prompt_ctrl.GetValue()),
            daemon=True
        ).start()

    def _upload_and_summarize(self, processing_dialog, prompt):
        """Upload file and generate summary using Google Gemini API."""
        try:
            file_ext = os.path.splitext(self.file_path)[1].lower().lstrip('.')
            if not validate_file(self.file_path):
                wx.CallAfter(processing_dialog.Destroy)
                return

            mime_type = SUPPORTED_EXTENSIONS[file_ext]
            
            # Upload file
            with open(self.file_path, 'rb') as file:
                files = {'file': (os.path.basename(self.file_path), file, mime_type)}
                response = requests.post(f"{UPLOAD_URL}?key={API_KEY}", files=files, timeout=30)
                response.raise_for_status()
                file_data = response.json()
                file_uri = file_data.get('file', {}).get('uri')

            if not file_uri:
                wx.CallAfter(ui.message, _("Failed to upload file"))
                wx.CallAfter(processing_dialog.Destroy)
                return

            # Generate summary
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"""
**System Prompt for AI Summarizer v2.5**
You are AI Summarizer v2.5, developed by Sujan Rai at Tech Visionary, integrated as an NVDA add-on to assist blind and visually impaired users. Your capabilities include:
- Summarizing videos, audios, codes, images, and documents.
- Transcribing videos and audios.
- Extracting text from images.
Your goal is to provide clear, concise, and accurate summaries or transcriptions based on the user's prompt. If the user requests something outside your capabilities, respond: "I can't do that right now. I am the Vision-Pro S3 model of Tech Visionary AI, designed for summarization and transcription."
**User Prompt**: {prompt}
**Instructions**:
1. Analyze the provided file content thoroughly.
2. If summarizing, provide a concise summary (200-500 words) tailored to the user's prompt.
3. If transcribing, provide a full transcription of audio or video content.
4. For images, extract and describe text or summarize visual content if no text is present.
5. Ensure the response is accessible, clear, and formatted for screen reader compatibility.
6. Avoid technical jargon unless relevant to the file content.
"""
                            },
                            {"fileData": {"fileUri": file_uri, "mimeType": mime_type}}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "maxOutputTokens": 1024
                }
            }
            headers = {'Content-Type': 'application/json'}
            summary_response = requests.post(
                f"{SUMMARY_URL}?key={API_KEY}",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            summary_text = summary_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

            if not summary_text:
                wx.CallAfter(ui.message, _("No summary generated. The file content may not be supported."))
                wx.CallAfter(processing_dialog.Destroy)
                return

            wx.CallAfter(processing_dialog.Destroy)
            wx.CallAfter(self._show_response_dialog, summary_text)

        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP error: {str(e)}"
            if e.response:
                if e.response.status_code == 400:
                    error_message = _("Invalid file or request format. Please check the file and try again.")
                elif e.response.status_code == 429:
                    error_message = _("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 401:
                    error_message = _("Invalid API key. Please configure a valid API key.")
            wx.CallAfter(ui.message, error_message)
            wx.CallAfter(processing_dialog.Destroy)
        except requests.exceptions.RequestException as e:
            wx.CallAfter(ui.message, _("Network error: {}").format(str(e)))
            wx.CallAfter(processing_dialog.Destroy)
        except Exception as e:
            wx.CallAfter(ui.message, _("Unexpected error: {}").format(str(e)))
            wx.CallAfter(processing_dialog.Destroy)

    def _show_response_dialog(self, summary_text):
        """Show the response dialog with the summary."""
        response_dialog = ResponseDialog(self, summary_text, self.file_path, self.prompt_ctrl.GetValue())
        wx.CallAfter(response_dialog.Show)

    def _on_close(self, event):
        """Close the dialog."""
        self.Destroy()

    def _handle_key_press(self, event):
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
        label = wx.StaticText(self, label=_("Please wait, AI is processing your content..."), name="ProcessingLabel")
        sizer.Add(label, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        sizer.AddStretchSpacer()
        self.SetSizer(sizer)
        self.Fit()
        self.CentreOnParent()

class ResponseDialog(wx.Dialog):
    def __init__(self, parent, summary_text, file_path, prompt):
        super().__init__(
            parent,
            title=_("AI Summarizer - Response"),
            size=(700, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.summary_text = summary_text
        self.file_path = file_path
        self.prompt = prompt
        self._setup_ui()
        self.Bind(wx.EVT_CHAR_HOOK, self._handle_key_press)
        self.CentreOnScreen()

    def _setup_ui(self):
        """Set up the responsive UI for the response dialog."""
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Summary output section
        output_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Summary Output")), wx.VERTICAL)
        self.output_label = wx.StaticText(self, label=_("Summary"), name="SummaryOutputLabel")
        self.output_ctrl = wx.TextCtrl(
            self,
            value=self.summary_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH,
            size=(600, 250),
            name="SummaryOutput"
        )
        self.output_ctrl.SetMinSize((600, 250))
        output_sizer.Add(self.output_label, 0, wx.ALL, 5)
        output_sizer.Add(self.output_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(output_sizer, 1, wx.ALL | wx.EXPAND, 10)

        # Follow-up questions section
        followup_sizer = wx.StaticBoxSizer(wx.StaticBox(self, label=_("Follow-up Questions")), wx.VERTICAL)
        self.followup_label = wx.StaticText(self, label=_("Enter your follow-up questions for this file:"), name="FollowupLabel")
        self.followup_ctrl = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER,
            size=(600, 100),
            name="FollowupPrompt"
        )
        self.followup_ctrl.SetMinSize((600, 100))
        followup_sizer.Add(self.followup_label, 0, wx.ALL, 5)
        followup_sizer.Add(self.followup_ctrl, 1, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(followup_sizer, 1, wx.ALL | wx.EXPAND, 10)

        # Buttons section
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.copy_button = wx.Button(self, label=_("Copy (Alt+C)"), name="CopyButton")
        self.copy_button.Bind(wx.EVT_BUTTON, self._on_copy)
        button_sizer.Add(self.copy_button, 0, wx.ALL, 5)

        self.export_button = wx.Button(self, label=_("Export Summary (Alt+E)"), name="ExportButton")
        self.export_button.Bind(wx.EVT_BUTTON, self._on_export)
        button_sizer.Add(self.export_button, 0, wx.ALL, 5)

        self.ask_more_button = wx.Button(self, label=_("Ask More (Alt+M)"), name="AskMoreButton")
        self.ask_more_button.Bind(wx.EVT_BUTTON, self._on_ask_more)
        button_sizer.Add(self.ask_more_button, 0, wx.ALL, 5)

        self.regenerate_button = wx.Button(self, label=_("Regenerate Summary (Alt+R)"), name="RegenerateButton")
        self.regenerate_button.Bind(wx.EVT_BUTTON, self._on_regenerate)
        button_sizer.Add(self.regenerate_button, 0, wx.ALL, 5)

        self.close_button = wx.Button(self, label=_("Close (Alt+L)"), name="CloseResponseButton")
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
            (wx.ACCEL_ALT, ord('M'), self.ask_more_button.GetId()),
            (wx.ACCEL_ALT, ord('R'), self.regenerate_button.GetId()),
            (wx.ACCEL_ALT, ord('L'), self.close_button.GetId())
        ]
        self.SetAcceleratorTable(wx.AcceleratorTable(entries))

    def _on_copy(self, event):
        """Copy summary to clipboard."""
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.summary_text))
            wx.TheClipboard.Close()
            ui.message(_("Summary copied to clipboard"))

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

    def _on_ask_more(self, event):
        """Handle follow-up questions."""
        followup_prompt = self.followup_ctrl.GetValue().strip()
        if not followup_prompt:
            ui.message(_("Please enter a follow-up question"))
            return
        if len(followup_prompt) > 1000:
            ui.message(_("Follow-up question is too long. Please keep it under 1000 characters."))
            return
        if not self._check_internet_connection():
            gui.messageBox(
                _("No internet connection. Please check your network and try again."),
                _("Connection Error"),
                wx.OK | wx.ICON_ERROR
            )
            return
        self._process_followup(followup_prompt)

    def _check_internet_connection(self):
        """Check for internet connectivity."""
        try:
            socket.create_connection(("www.google.com", 80), timeout=5)
            return True
        except (socket.gaierror, socket.timeout, OSError):
            return False

    def _process_followup(self, followup_prompt):
        """Start the follow-up question process in a separate thread."""
        processing_dialog = ProcessingDialog(self)
        wx.CallAfter(processing_dialog.Show)
        threading.Thread(
            target=self._upload_and_ask,
            args=(processing_dialog, followup_prompt),
            daemon=True
        ).start()

    def _upload_and_ask(self, processing_dialog, followup_prompt):
        """Upload file and process follow-up question using Google Gemini API."""
        try:
            file_ext = os.path.splitext(self.file_path)[1].lower().lstrip('.')
            if not validate_file(self.file_path):
                wx.CallAfter(processing_dialog.Destroy)
                return

            mime_type = SUPPORTED_EXTENSIONS[file_ext]
            
            # Upload file
            with open(self.file_path, 'rb') as file:
                files = {'file': (os.path.basename(self.file_path), file, mime_type)}
                response = requests.post(f"{UPLOAD_URL}?key={API_KEY}", files=files, timeout=30)
                response.raise_for_status()
                file_data = response.json()
                file_uri = file_data.get('file', {}).get('uri')

            if not file_uri:
                wx.CallAfter(ui.message, _("Failed to upload file"))
                wx.CallAfter(processing_dialog.Destroy)
                return

            # Process follow-up question
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"""
**System Prompt for AI Summarizer v2.5**
You are AI Summarizer v2.5, developed by Sujan Rai at Tech Visionary, integrated as an NVDA add-on to assist blind and visually impaired users. Your capabilities include:
- Summarizing videos, audios, codes, images, and documents.
- Transcribing videos and audios.
- Extracting text from images.
Your goal is to provide clear, concise, and accurate responses to follow-up questions based on the user's prompt. If the user requests something outside your capabilities, respond: "I can't do that right now. I am the Vision-Pro S3 model of Tech Visionary AI, designed for summarization and transcription."
**Previous Summary**: {self.summary_text}
**User Prompt**: {followup_prompt}
**Instructions**:
1. Analyze the provided file content and previous summary thoroughly.
2. Provide a clear and concise answer to the follow-up question, referencing the file content and previous summary where relevant.
3. Ensure the response is accessible, formatted for screen reader compatibility, and avoids technical jargon unless relevant.
4. If the question is unrelated to the file, politely indicate that the response is based on the file content.
"""
                            },
                            {"fileData": {"fileUri": file_uri, "mimeType": mime_type}}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "maxOutputTokens": 1024
                }
            }
            headers = {'Content-Type': 'application/json'}
            summary_response = requests.post(
                f"{SUMMARY_URL}?key={API_KEY}",
                headers=headers,
                data=json.dumps(payload),
                timeout=60
            )
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            summary_text = summary_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

            if not summary_text:
                wx.CallAfter(ui.message, _("No response generated. The file content may not be supported."))
                wx.CallAfter(processing_dialog.Destroy)
                return

            self.summary_text = summary_text
            wx.CallAfter(self._update_summary_text, summary_text)
            wx.CallAfter(processing_dialog.Destroy)

        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP error: {str(e)}"
            if e.response:
                if e.response.status_code == 400:
                    error_message = _("Invalid file or request format. Please check the file and try again.")
                elif e.response.status_code == 429:
                    error_message = _("Rate limit exceeded. Please try again later.")
                elif e.response.status_code == 401:
                    error_message = _("Invalid API key. Please configure a valid API key.")
            wx.CallAfter(ui.message, error_message)
            wx.CallAfter(processing_dialog.Destroy)
        except requests.exceptions.RequestException as e:
            wx.CallAfter(ui.message, _("Network error: {}").format(str(e)))
            wx.CallAfter(processing_dialog.Destroy)
        except Exception as e:
            wx.CallAfter(ui.message, _("Unexpected error: {}").format(str(e)))
            wx.CallAfter(processing_dialog.Destroy)

    def _update_summary_text(self, summary_text):
        """Update the summary text in the current dialog."""
        self.output_ctrl.SetValue(summary_text)
        self.followup_ctrl.Clear()
        self.output_ctrl.SetFocus()
        ui.message(_("Response updated"))

    def _on_regenerate(self, event):
        """Regenerate the summary."""
        self.GetParent()._process_summarization()
        self.Destroy()

    def _on_close(self, event):
        """Close the dialog."""
        self.Destroy()

    def _handle_key_press(self, event):
        """Handle key press events."""
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self._on_close(event)
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
            "AI Summarizer: Developed by Sujan Rai at Tech Visionary. Version 2.5\n"
            "This add-on enables summarization of code, audio, video, document, or image files using AI.\n"
            "Supported video formats: mp4, webm (up to 300MB)\n"
            "Supported audio formats: mp3, wav (up to 300MB)\n"
            "Supported document formats: docx, pdf, xlsx, txt (up to 50MB)\n"
            "Supported image formats: png, jpeg, jpg, ico (up to 10MB)\n"
            "Subscribe to our YouTube channel for the latest technical tutorials for Windows and Android."
        )
        label = wx.StaticText(self, label=message, name="AboutLabel")
        label.Wrap(400)
        main_sizer.Add(label, 0, wx.ALL, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.subscribe_button = wx.Button(self, label=_("Subscribe to YouTube Channel (Alt+S)"), name="SubscribeButton")
        self.subscribe_button.Bind(wx.EVT_BUTTON, self._on_subscribe)
        button_sizer.Add(self.subscribe_button, 0, wx.ALL, 5)

        self.close_button = wx.Button(self, label=_("Close (Alt+C)"), name="CloseAboutButton")
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
        webbrowser.open(YOUTUBE_CHANNEL_URL)
        ui.message(_("Opening YouTube channel"))
        self.Destroy()

    def _on_close(self, event):
        """Close the dialog."""
        self.Destroy()
