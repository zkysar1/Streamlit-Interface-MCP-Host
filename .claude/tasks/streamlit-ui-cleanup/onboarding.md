# Task Onboarding: Streamlit UI Cleanup

## Task Overview
The user wants to clean up the Streamlit chat interface to make the progress reporting less verbose and more user-friendly. The main issues are:
1. Too many progress updates cluttering the UI
2. The 30-second timeout messages create new lines instead of updating in place
3. Control buttons (stop/clear) should float at the bottom of the robot's response
4. Consider hiding details with expandable sections

## Current System Architecture

### Frontend (Streamlit)
- **Main File**: `pages/BasicChat.py`
- **Progress Display**: Lines 56-133 handle different event types from SSE stream
- **Message Display**: Uses `st.markdown()` with cumulative string concatenation (line 332)
- **Control Buttons**: Fixed position above chat input (lines 294-315)

### Backend (Java)
- **Streaming Handler**: `StreamingConversationHandler.java` forwards events to SSE
- **Progress Publisher**: `StreamingEventPublisher.java` creates detailed progress events
- **Orchestration Timer**: `OrchestrationStrategy.java` has 5-second periodic updates
  - Configured in `orchestration-strategies.json` with `progress_update_interval_ms: 5000`
  - Timer ID stored in `progressTimerId` array
  - Creates "Processing oracle_full_pipeline... (Xms)" messages

## Key Issues Identified

### 1. Excessive Progress Events
The system publishes numerous types of progress events:
- `tool_selection` events with strategy details
- `tool_analysis` events with tool requirements
- `tool_execution` events for each tool call
- `tool_routing` events for MCP routing
- `tool_completed` events
- Periodic "Processing..." updates every 5 seconds
- Detailed phase events (llm_request, llm_response, sql_query, etc.)

### 2. Progress Timer Implementation
- Located in `OrchestrationStrategy.java` lines 682-702
- Uses `vertx.setPeriodic(5000, ...)` to create recurring updates
- Sends cumulative elapsed time: "Processing oracle_full_pipeline... (10002ms)"
- Creates new lines in frontend instead of updating in place

### 3. UI Layout Issues
- Progress messages accumulate in `full_response` string (line 331)
- Each event appends with `\n\n` creating vertical sprawl
- Control buttons are statically positioned, not floating with content
- No collapsible sections for detailed information

## Solution Approach

### Phase 1: Reduce Verbosity
1. **Filter Events at Frontend**
   - Only show high-level progress (tool calls, major phases)
   - Skip intermediate routing/analysis events
   - Consolidate related events

2. **Simplify Progress Messages**
   - Remove duplicate information
   - Use concise status indicators
   - Group related operations

### Phase 2: Update Progress Display
1. **Replace Cumulative Timer**
   - Use single updating line for "Working... (X seconds)"
   - Leverage `st.empty()` container for in-place updates
   - Show elapsed time without creating new lines

2. **Implement Progress Container**
   - Separate progress area from final response
   - Clear progress when operation completes
   - Show only relevant current status

### Phase 3: Improve UI Layout
1. **Floating Controls**
   - Move buttons inside chat message container
   - Position at bottom of assistant's current response
   - Use Streamlit columns for layout

2. **Collapsible Details**
   - Use `st.expander()` for verbose information
   - Default to collapsed state
   - Allow user to expand for debugging

### Phase 4: Backend Optimization (Optional)
1. **Configure Progress Frequency**
   - Increase interval or make configurable
   - Add event filtering at source
   - Reduce redundant event publishing

## Implementation Details

### Key Code Locations
- **Frontend Event Handling**: `BasicChat.py` lines 48-185
- **Progress Display Logic**: `BasicChat.py` lines 326-336
- **Backend Timer**: `OrchestrationStrategy.java` lines 114-116, 682-702
- **Event Publisher**: `StreamingEventPublisher.java` entire file
- **SSE Handler**: `StreamingConversationHandler.java` lines 122-134

### Event Types to Handle
- `connected` - Connection established
- `progress` - Various progress updates
- `tool_call_start` - Tool execution beginning
- `tool_call_complete` - Tool execution finished
- `execution_paused` - User interrupt
- `agent_question` - Agent needs input
- `final_response` - Actual response content
- `error` - Error messages
- `done` - Stream complete

### Testing Considerations
- Test with long-running Oracle queries
- Verify interrupt functionality still works
- Ensure no loss of critical information
- Check mobile/narrow viewport behavior
- Test with multiple concurrent operations

## Next Steps
1. Create a more elegant progress display system
2. Implement smart event filtering
3. Add UI controls for verbosity level
4. Test with various query types
5. Get user feedback and iterate