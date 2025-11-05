import sys
import json
from pathlib import Path
from docling_ocr import create_ocr_processor


def main():
    print("=" * 80)
    print("🔍 DOCLING OCR - IMAGE TEXT EXTRACTION")
    print("=" * 80)
    print()
    
    # Check arguments
    if len(sys.argv) < 2:
        print("❌ Error: No image path provided")
        print("\n📖 Usage:")
        print("   python run_ocr.py <image_path>")
        print("   python run_ocr.py data/scan.jpg")
        print("   python run_ocr.py data/images/  (process folder)")
        print()
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize OCR
        print("🔧 Initializing OCR engine...")
        ocr = create_ocr_processor()
        print()
        
        # Process input
        if input_path.is_file():
            # Single file
            result = ocr.process_image(str(input_path), enhance=False)
            
            if result['success']:
                # Save result
                output_file = output_dir / f"{input_path.stem}_ocr.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                # Print summary
                print("\n" + "=" * 80)
                print("✅ EXTRACTION SUCCESSFUL")
                print("=" * 80)
                print(f"\n📄 File: {result['file_name']}")
                print(f"📊 Quality: {result['metadata']['quality'].upper()}")
                print(f"📈 Confidence: {result['metadata']['confidence_score']:.1%}")
                print(f"📝 Words extracted: {result['metadata']['word_count']}")
                print(f"\n💾 Output saved to: {output_file}")
                
                # Show preview
                preview = result['extracted_text'][:500]
                print(f"\n📖 Text Preview:")
                print("-" * 80)
                print(preview + "..." if len(result['extracted_text']) > 500 else preview)
                print("-" * 80)
                
                # Warnings
                if 'warnings' in result:
                    print("\n⚠️  Warnings:")
                    for warning in result['warnings']:
                        print(f"   • {warning}")
                
                print()
                
            else:
                print("\n❌ EXTRACTION FAILED")
                print(f"Error: {result['error']}")
                sys.exit(1)
        
        elif input_path.is_dir():
            # Folder
            summary = ocr.process_folder(str(input_path), output_dir=str(output_dir), enhance=True)
            
            print("\n" + "=" * 80)
            print("✅ BATCH PROCESSING COMPLETE")
            print("=" * 80)
            print(f"\n📁 Folder: {summary['folder']}")
            print(f"📊 Total files: {summary['total_files']}")
            print(f"✅ Successful: {summary['successful']}")
            print(f"❌ Failed: {summary['failed']}")
            print(f"\n💾 Results saved to: {output_dir}/")
            print(f"💾 Summary: {output_dir}/batch_summary.json")
            print()
        
        else:
            print(f"❌ Error: Path not found: {input_path}")
            sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
