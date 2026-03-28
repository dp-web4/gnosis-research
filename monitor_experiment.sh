#!/bin/bash
# Monitor tool-use conversation experiment and display updates

LOGFILE="tool_use_conversation_output.log"
EXPECTED_TURNS=40

while true; do
    if [ ! -f "$LOGFILE" ]; then
        echo "Waiting for log file..."
        sleep 10
        continue
    fi

    # Count completed turns
    TURNS=$(grep -c "Pre-turn:" "$LOGFILE" || echo 0)

    # Check if experiment finished
    if grep -q "Calculating results..." "$LOGFILE"; then
        echo "============================================"
        echo "EXPERIMENT COMPLETE!"
        echo "============================================"
        break
    fi

    # Display progress
    clear
    echo "=========================================="
    echo "Tool-Use Conversation Experiment Monitor"
    echo "=========================================="
    echo ""
    echo "Turns completed: $TURNS / $EXPECTED_TURNS"
    echo "Progress: $(python3 -c "print(f'{$TURNS/$EXPECTED_TURNS*100:.1f}%')")"
    echo ""
    echo "Current state distribution:"
    grep "Pre-turn.*State=" "$LOGFILE" 2>/dev/null | sed 's/.*State=\([a-z]*\).*/\1/' | sort | uniq -c
    echo ""
    echo "Latest turn:"
    tail -6 "$LOGFILE"
    echo ""
    echo "Refreshing every 30 seconds... (Ctrl+C to stop)"

    sleep 30
done

echo ""
echo "Experiment complete! Analyzing results..."
echo ""
