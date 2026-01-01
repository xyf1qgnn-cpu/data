# Discovery Questions

**Phase**: Discovery
**Date**: 2026-01-01 15:28
**Total Questions**: 5

## Q1: Does the existing data extraction workflow need to remain fully functional in the GUI version?
**Default if unknown:** Yes (the GUI should preserve all existing functionality)
**Reasoning:** The GUI is meant to package the existing workflow, not replace it. All PDF processing, AI extraction, validation, and Excel export features should work exactly as they do in the command-line version.

## Q2: Should the GUI application support batch processing of multiple PDF files simultaneously?
**Default if unknown:** Yes (based on requirement to process "all PDF files in that path")
**Reasoning:** The requirement states "对该路径下的所有pdf文件进行处理" (process all PDF files in that path), which implies batch processing capability.

## Q3: Should the API key be saved between application sessions for convenience?
**Default if unknown:** Yes (users shouldn't need to re-enter API key every time)
**Reasoning:** While the API key shouldn't be hardcoded, it's reasonable to save it locally (encrypted) for user convenience across multiple sessions.

## Q4: Does the application need to run on Windows only, or also support macOS/Linux?
**Default if unknown:** Windows only (specifically mentions .exe file)
**Reasoning:** The requirement specifically mentions ".exe file", which is a Windows executable format. However, we should clarify if cross-platform support is needed.

## Q5: Should the GUI include advanced configuration options beyond API key input?
**Default if unknown:** No (keep it simple, focus on core requirements)
**Reasoning:** The requirements specify only API key input via GUI. Additional configuration could be added later if needed, but initial version should focus on core functionality.