#!/bin/bash
# Export all Layer 4 queries to JSON

echo "🚀 Starting JSON export for all Layer 4 queries..."
echo "=================================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the JSON exporter with verification
echo "📊 Exporting queries to JSON format..."
python3 json_exporter.py --verify --min-rows 10

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Export completed successfully!"
    echo "📁 JSON files saved to: exports/"
    echo ""
    
    # Count files
    file_count=$(ls -1 exports/*.json 2>/dev/null | wc -l)
    echo "📊 Total JSON files: $file_count"
else
    echo ""
    echo "❌ Export failed. Check error messages above."
    exit 1
fi