"""
OCR Quality Analyzer
Analyzes extraction results and generates detailed reports
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import Counter
import shutil


class OCRAnalyzer:
    """Analyze OCR results and generate reports"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def analyze_result(self, result: Dict) -> Dict:
        """
        Analyze single image result and determine failure reason
        Returns enriched result with analysis
        """
        analysis = {
            'status': 'unknown',
            'quality_category': 'unknown',
            'needs_review': False,
            'failure_reason': None,
            'recommendations': []
        }
        
        if not result.get('success'):
            # Complete failure
            analysis['status'] = 'failed'
            analysis['quality_category'] = 'failed'
            analysis['needs_review'] = True
            
            # Determine failure reason
            error = result.get('error', '')
            if 'not found' in error.lower():
                analysis['failure_reason'] = 'File not found'
            elif 'unsupported format' in error.lower():
                analysis['failure_reason'] = 'Unsupported file format'
            else:
                analysis['failure_reason'] = 'Processing error'
            
            analysis['recommendations'] = ['Manual entry required']
            
        else:
            # Successful processing - analyze quality
            metadata = result.get('metadata', {})
            confidence = metadata.get('confidence_score', 0.0)
            word_count = metadata.get('word_count', 0)
            
            # Categorize based on confidence and content
            if confidence >= 0.85 and word_count >= 10:
                analysis['status'] = 'success'
                analysis['quality_category'] = 'excellent'
                analysis['needs_review'] = False
                
            elif confidence >= 0.70 and word_count >= 5:
                analysis['status'] = 'success'
                analysis['quality_category'] = 'good'
                analysis['needs_review'] = False
                analysis['recommendations'] = ['Spot check recommended (10% sample)']
                
            elif confidence >= 0.50 and word_count >= 3:
                analysis['status'] = 'success'
                analysis['quality_category'] = 'fair'
                analysis['needs_review'] = True
                analysis['recommendations'] = ['Verify extracted text accuracy']
                
            elif word_count == 0:
                # No text extracted
                analysis['status'] = 'failed'
                analysis['quality_category'] = 'no_text'
                analysis['needs_review'] = True
                
                # Diagnose why
                image_size = metadata.get('image_size', [0, 0])
                min_dimension = min(image_size) if image_size else 0
                
                if min_dimension < 500:
                    analysis['failure_reason'] = 'Image too small/low resolution'
                    analysis['recommendations'] = ['Use higher resolution scan (>1000px)']
                else:
                    analysis['failure_reason'] = 'Blank or non-text image'
                    analysis['recommendations'] = ['Verify image contains readable text', 'Check if image is correct file']
                
            else:
                # Low confidence
                analysis['status'] = 'success'
                analysis['quality_category'] = 'poor'
                analysis['needs_review'] = True
                
                # Diagnose likely issues
                reasons = []
                if confidence < 0.30:
                    reasons.append('Very low OCR confidence')
                if word_count < 5:
                    reasons.append('Very few words extracted')
                
                # Check image characteristics
                image_size = metadata.get('image_size', [0, 0])
                min_dimension = min(image_size) if image_size else 0
                
                if min_dimension < 800:
                    reasons.append('Small image size')
                    analysis['recommendations'].append('Rescan at higher resolution')
                
                analysis['failure_reason'] = ' + '.join(reasons) if reasons else 'Poor quality/unclear text'
                analysis['recommendations'].append('Consider manual entry or re-scanning')
        
        return analysis
    
    def generate_batch_report(self, batch_results: Dict) -> Dict:
        """
        Generate comprehensive analysis report for batch processing
        """
        results = batch_results.get('results', [])
        
        # Analyze each result
        analyzed_results = []
        for result in results:
            analysis = self.analyze_result(result)
            result['analysis'] = analysis
            analyzed_results.append(result)
        
        # Aggregate statistics
        total = len(analyzed_results)
        
        # Count by quality category
        categories = Counter([r['analysis']['quality_category'] for r in analyzed_results])
        
        # Count by status
        statuses = Counter([r['analysis']['status'] for r in analyzed_results])
        
        # Collect failure reasons
        failure_reasons = Counter([
            r['analysis']['failure_reason'] 
            for r in analyzed_results 
            if r['analysis']['failure_reason']
        ])
        
        # Images needing review
        review_needed = [
            r for r in analyzed_results 
            if r['analysis']['needs_review']
        ]
        
        # Build summary
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_images': total,
            'summary': {
                'successful': statuses.get('success', 0),
                'failed': statuses.get('failed', 0),
                'needs_review': len(review_needed)
            },
            'quality_breakdown': {
                'excellent': categories.get('excellent', 0),
                'good': categories.get('good', 0),
                'fair': categories.get('fair', 0),
                'poor': categories.get('poor', 0),
                'no_text': categories.get('no_text', 0),
                'failed': categories.get('failed', 0)
            },
            'failure_reasons': dict(failure_reasons),
            'review_queue': [
                {
                    'file_name': r['file_name'],
                    'quality': r['analysis']['quality_category'],
                    'confidence': r.get('metadata', {}).get('confidence_score', 0.0),
                    'reason': r['analysis']['failure_reason'],
                    'recommendations': r['analysis']['recommendations']
                }
                for r in review_needed
            ],
            'detailed_results': analyzed_results
        }
        
        return report
    
    def save_report(self, report: Dict, batch_summary_path: str = None):
        """Save comprehensive reports in multiple formats"""
        
        # 1. Save detailed JSON report
        json_report_path = self.output_dir / 'extraction_analysis.json'
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Detailed report: {json_report_path}")
        
        # 2. Generate HTML dashboard
        html_report = self._generate_html_report(report)
        html_report_path = self.output_dir / 'extraction_analysis.html'
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"💾 Visual dashboard: {html_report_path}")
        
        # 3. Copy failed images to separate folder
        failed_dir = self.output_dir / 'failed_images'
        failed_dir.mkdir(exist_ok=True)
        
        failed_count = 0
        for result in report['review_queue']:
            if result['quality'] in ['no_text', 'failed', 'poor']:
                source = Path(result.get('file_path', ''))
                if source.exists():
                    dest = failed_dir / result['file_name']
                    shutil.copy2(source, dest)
                    failed_count += 1
        
        if failed_count > 0:
            print(f"💾 Failed images copied: {failed_dir}/ ({failed_count} files)")
        
        # 4. Print console summary
        self._print_summary(report)
    
    def _print_summary(self, report: Dict):
        """Print formatted summary to console"""
        print("\n" + "=" * 80)
        print("📊 EXTRACTION ANALYSIS REPORT")
        print("=" * 80)
        
        total = report['total_images']
        summary = report['summary']
        quality = report['quality_breakdown']
        
        print(f"\nTotal Images: {total}")
        
        # Success breakdown
        print(f"\n✅ SUCCESSFUL EXTRACTIONS: {summary['successful']} ({summary['successful']/total*100:.1f}%)")
        if quality['excellent'] > 0:
            print(f"   Excellent (>85% confidence): {quality['excellent']} images ({quality['excellent']/total*100:.1f}%)")
        if quality['good'] > 0:
            print(f"   Good (70-85% confidence): {quality['good']} images ({quality['good']/total*100:.1f}%)")
        if quality['fair'] > 0:
            print(f"   Fair (50-69% confidence): {quality['fair']} images ({quality['fair']/total*100:.1f}%)")
        
        # Issues
        needs_review = summary['needs_review']
        if needs_review > 0:
            print(f"\n⚠️  NEEDS REVIEW: {needs_review} images ({needs_review/total*100:.1f}%)")
            if quality['poor'] > 0:
                print(f"   Poor quality (<50% confidence): {quality['poor']} images")
            if quality['no_text'] > 0:
                print(f"   No text extracted: {quality['no_text']} images")
        
        # Failures
        failed = summary['failed']
        if failed > 0:
            print(f"\n❌ FAILED EXTRACTIONS: {failed} images ({failed/total*100:.1f}%)")
            
            # Failure reasons
            if report['failure_reasons']:
                print(f"\n📋 FAILURE REASONS:")
                for i, (reason, count) in enumerate(report['failure_reasons'].items(), 1):
                    print(f"   {i}. {reason}: {count} images")
        
        print("\n" + "=" * 80)
    
    def _generate_html_report(self, report: Dict) -> str:
        """Generate HTML dashboard"""
        total = report['total_images']
        summary = report['summary']
        quality = report['quality_breakdown']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OCR Extraction Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .stat-card.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
        .stat-card.failed {{ background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%); }}
        .stat-value {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .quality-breakdown {{ margin: 30px 0; }}
        .quality-bar {{ background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden; margin: 10px 0; }}
        .quality-segment {{ height: 100%; float: left; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; font-weight: bold; }}
        .excellent {{ background: #4CAF50; }}
        .good {{ background: #8BC34A; }}
        .fair {{ background: #FFC107; }}
        .poor {{ background: #FF9800; }}
        .no-text {{ background: #FF5722; }}
        .failed {{ background: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 OCR Extraction Analysis Report</h1>
        <p class="timestamp">Generated: {report['timestamp']}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Images</div>
                <div class="stat-value">{total}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Successful</div>
                <div class="stat-value">{summary['successful']}</div>
                <div class="stat-label">{summary['successful']/total*100:.1f}%</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Needs Review</div>
                <div class="stat-value">{summary['needs_review']}</div>
                <div class="stat-label">{summary['needs_review']/total*100:.1f}%</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-label">Failed</div>
                <div class="stat-value">{summary['failed']}</div>
                <div class="stat-label">{summary['failed']/total*100:.1f}%</div>
            </div>
        </div>
        
        <h2>Quality Breakdown</h2>
        <div class="quality-bar">
            <div class="quality-segment excellent" style="width: {quality['excellent']/total*100:.1f}%">
                Excellent ({quality['excellent']})
            </div>
            <div class="quality-segment good" style="width: {quality['good']/total*100:.1f}%">
                Good ({quality['good']})
            </div>
            <div class="quality-segment fair" style="width: {quality['fair']/total*100:.1f}%">
                Fair ({quality['fair']})
            </div>
            <div class="quality-segment poor" style="width: {quality['poor']/total*100:.1f}%">
                Poor ({quality['poor']})
            </div>
            <div class="quality-segment no-text" style="width: {quality['no_text']/total*100:.1f}%">
                No Text ({quality['no_text']})
            </div>
            <div class="quality-segment failed" style="width: {quality['failed']/total*100:.1f}%">
                Failed ({quality['failed']})
            </div>
        </div>
        
        <h2>Review Queue ({len(report['review_queue'])} images)</h2>
        <table>
            <tr>
                <th>File Name</th>
                <th>Quality</th>
                <th>Confidence</th>
                <th>Issue</th>
                <th>Recommendations</th>
            </tr>
"""
        
        for item in report['review_queue'][:50]:  # Show top 50
            html += f"""
            <tr>
                <td>{item['file_name']}</td>
                <td>{item['quality']}</td>
                <td>{item['confidence']:.1%}</td>
                <td>{item['reason'] or 'N/A'}</td>
                <td>{'; '.join(item['recommendations'][:2])}</td>
            </tr>
"""
        
        html += """
        </table>
    </div>
</body>
</html>
"""
        return html


def analyze_batch_results(batch_summary_path: str, output_dir: str = "output"):
    """
    Convenience function to analyze existing batch results
    """
    with open(batch_summary_path, 'r', encoding='utf-8') as f:
        batch_results = json.load(f)
    
    analyzer = OCRAnalyzer(output_dir=output_dir)
    report = analyzer.generate_batch_report(batch_results)
    analyzer.save_report(report)
    
    return report
