# Detail Answers

**Phase**: Detail Requirements
**Date**: 2026-01-01 15:28
**Total Questions**: 5
**Answered**: 5

## Q1: Should the GUI preserve the existing directory structure (files/, NotInput/, Excluded/) or allow custom output locations?
**Answer:** Preserve with customization
**Details:** Keep existing directory names by default but allow users to choose custom locations via GUI settings.

## Q2: Should the progress bar show overall progress (files processed/total) or detailed per-file progress with time estimates?
**Answer:** Both - comprehensive display
**Details:** Show overall progress bar plus detailed per-file status in log area with time estimates when possible.

## Q3: Should the application include a "dry run" or preview mode that extracts data without calling the API?
**Answer:** No - focus on core
**Details:** Skip preview mode to keep initial version simple and focused on reliable batch processing.

## Q4: Should error handling include automatic retry for failed API calls with configurable retry limits?
**Answer:** Yes - basic retry
**Details:** Implement basic retry logic (3 attempts with exponential backoff) for transient API failures.

## Q5: Should the application include export options beyond Excel (CSV, JSON) in the initial version?
**Answer:** Excel only
**Details:** Maintain existing Excel export with styling and validation highlighting as the sole output format.

## Summary of Technical Decisions:
1. **Directory Structure**: Default to existing structure with GUI customization options
2. **Progress Display**: Comprehensive display with overall progress bar and detailed per-file logs
3. **Preview Mode**: Not included in initial version - focus on core functionality
4. **Error Handling**: Basic retry logic for API calls (3 attempts with backoff)
5. **Export Formats**: Excel only, preserving existing styling and validation highlighting

## Implementation Implications:
- Need to add directory selection to GUI settings
- Progress reporting must include both overall and per-file details
- API client needs retry wrapper with exponential backoff
- Excel export remains unchanged from existing implementation
- No additional export format development required