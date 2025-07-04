# AI Summarizer NVDA Add-on

## Introduction
The AI Summarizer is an innovative NVDA add-on designed to leverage AI capabilities for summarizing various types of content, including code, audio, video, documents, and images. Developed by Sujan Rai at Team of Tech Visionary, this add-on integrates with the Google Gemini API to provide concise and accurate summaries, enhancing accessibility for NVDA users.

## Description
The AI Summarizer NVDA Add-on enables users to upload files in supported formats and generate AI-driven summaries based on customizable prompts. It features a user-friendly interface with a main dialog for file selection and prompt input, a response dialog for viewing summaries, and an about dialog for add-on information. The add-on is designed to be accessible, with keyboard shortcuts and responsive UI elements tailored for NVDA users.

## Features
- **File Support**: Summarize a wide range of file types, including:
  - Video: MP4, MKV
  - Audio: MP3, WAV
  - Images: PNG, JPEG, JPG, ICO
- **Customizable Prompts**: Users can specify how they want the AI to describe or summarize their content.
- **Responsive UI**: Dialogs are designed with accessibility in mind, featuring keyboard shortcuts and clear navigation.
- **Clipboard and Export Options**: Copy summaries to the clipboard or export them as text files.
- **Internet Connectivity Check**: Ensures reliable operation by verifying internet access before processing.
- **Threaded Processing**: Summarization runs in a separate thread to keep the UI responsive.

## Key Features
- **AI-Powered Summarization**: introduces AISummarizer v2.5 for high-quality content summarization.
- **Accessible Interface**: Fully compatible with NVDA, with keyboard gestures and screen reader feedback.
**transcription**: now v2.5 can transcribe the audios and videos.
**text extraction** v2.5 can extract the text from an image.

## Gestures
- **NVDA+Alt+N**: Opens the AI Summarizer dialog.
- **Alt+A**: Attach a file in the main dialog.
- **Alt+R**: Remove the attached file in the main dialog.
- **Alt+S**: Summarize the content in the main dialog or subscribe to the YouTube channel in the about dialog.
- **Alt+B**: Open the about dialog or go back to the main dialog from the response dialog.
- **Alt+C**: Close any dialog or copy the summary to the clipboard in the response dialog.
- **Alt+E**: Export the summary to a text file in the response dialog.
- **Alt+L**: Close the response dialog.
- **Escape**: Close any dialog.
- **Backspace**: Return to the main dialog from the response dialog.

## Instructions
1. **Install the Add-on**:
   - Download the add-on from the official repository or NVDA add-on store.

2. **Access the Add-on**:
   - Use `NVDA+Alt+N` to open the AI Summarizer dialog, or navigate to the "AI Summarizer" menu in NVDA's tools menu.

3. **Summarize Content**:
   - In the main dialog, enter a prompt describing how you want the AI to summarize your content.
   - Click "Attach a file (Alt+A)" or press `Alt+A` to select a supported file.
   - Click "Summarize (Alt+S)" or press `Alt+S` to process the file.
   - Wait for the AI to generate the summary, shown in the response dialog.

4. **Manage Summaries**:
   - In the response dialog, view the summary, copy it to the clipboard (`Alt+C`), or export it as a text file (`Alt+E`).
   - Regenerate the summary (`Alt+R`) or return to the main dialog (`Alt+B`).

5. **Learn More**:
   - Access the about dialog via the tools menu or `Alt+B` in the main dialog to view add-on details and subscribe to the YouTube channel.

### update info
updated to v2.5.

### change logs
**video files support**
now this add-on can summarize video files.
previous version had issues which i have fixed all.
**follow up questions**
now you can ask AI follow up questions.
for example: if you have generated a summary, you can ask the AI the questions again.
**transcription support**
now, AISummarizer v2.5 pro introduces a transcription feature among all of you.
upload a supported file and ask the AI to transcribe the audio or video.
**image text extraction**
now, v2.5 introduces image text extraction with AI.
upload a supported extention of image and ask the AI to extract the text.
many more features are comming soon.

## Note
- An active internet connection is required for summarization, as the add-on relies on the Google Gemini API.
- Only supported file formats listed above can be processed.
- For the latest tutorials and updates, subscribe to the Team of Tech Visionary YouTube channel at [https://youtube.com/@blindtechvisionary](https://youtube.com/@blindtechvisionary).

## License
This add-on is licensed under the **GNU General Public License v2 (GPLv2)**. See the license file for details.

## Contributions
Contributions are welcome! Visit our GitHub repository at [https://github.com/s-toolkit/ai-summarizer-nvda-addon](https://github.com/s-toolkit/ai-summarizer-nvda-addon) to contribute, report issues, or suggest improvements.

## Home Page
For more information, visit the project home page at [https://github.com/s-toolkit/ai-summarizer-nvda-addon](https://github.com/s-toolkit/ai-summarizer-nvda-addon).