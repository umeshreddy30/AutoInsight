"""
Report Generation Service
Creates professional PDF and HTML reports
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from jinja2 import Template
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import markdown

from app.config import settings
from app.utils.logger import app_logger as logger
from app.models.schemas import VisualizationData, LLMInsight


class ReportGenerator:
    """Professional report generation service"""
    
    def __init__(self, analysis_id: str):
        """Initialize report generator"""
        self.analysis_id = analysis_id
        self.report_dir = settings.REPORT_DIR / analysis_id
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_pdf_report(
        self,
        dataset_info: Dict[str, Any],
        column_stats: List[Dict[str, Any]],
        correlations: Dict[str, Any],
        outliers: List[Dict[str, Any]],
        data_quality: Dict[str, Any],
        insights: List[LLMInsight],
        visualizations: List[VisualizationData]
    ) -> str:
        """Generate comprehensive PDF report"""
        
        filepath = self.report_dir / f"report_{self.analysis_id}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for report elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Title Page
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("AutoInsight", title_style))
        elements.append(Paragraph("Automated Data Analysis Report", styles['Heading2']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Report metadata
        metadata_data = [
            ['Report ID:', self.analysis_id],
            ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Dataset Size:', f"{dataset_info['rows']:,} rows × {dataset_info['columns']} columns"],
            ['Data Quality:', f"{data_quality['completeness_percentage']:.1f}% complete"]
        ]
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(metadata_table)
        elements.append(PageBreak())
        
        # Executive Summary from AI
        elements.append(Paragraph("Executive Summary", heading_style))
        for insight in insights:
            if insight.section == "Executive Summary":
                paragraphs = insight.content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        elements.append(Paragraph(para.strip(), body_style))
                break
        elements.append(Spacer(1, 0.3*inch))
        
        # Data Quality Assessment
        elements.append(Paragraph("Data Quality Assessment", heading_style))
        quality_data = [
            ['Metric', 'Value'],
            ['Total Rows', f"{data_quality['total_rows']:,}"],
            ['Total Columns', f"{data_quality['total_columns']}"],
            ['Missing Cells', f"{data_quality['missing_cells']:,}"],
            ['Completeness', f"{data_quality['completeness_percentage']:.2f}%"],
            ['Duplicate Rows', f"{data_quality['duplicate_rows']:,}"],
            ['Memory Usage', f"{data_quality['memory_usage_mb']:.2f} MB"]
        ]
        quality_table = Table(quality_data, colWidths=[3*inch, 3*inch])
        quality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(quality_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # AI Insights sections
        for insight in insights:
            if insight.section != "Executive Summary":
                elements.append(Paragraph(insight.section, heading_style))
                paragraphs = insight.content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        elements.append(Paragraph(para.strip(), body_style))
                elements.append(Spacer(1, 0.2*inch))
        
        elements.append(PageBreak())
        
        # Column Statistics
        elements.append(Paragraph("Column Statistics Summary", heading_style))
        for col_stat in column_stats[:10]:  # Top 10
            elements.append(Paragraph(f"<b>{col_stat['name']}</b> ({col_stat['dtype']})", styles['Heading3']))
            
            stats_text = f"Missing: {col_stat['null_percentage']:.1f}% | Unique: {col_stat['unique_count']:,}"
            elements.append(Paragraph(stats_text, body_style))
            
            if col_stat.get('stats'):
                stats = col_stat['stats']
                if 'mean' in stats:
                    detail = f"Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}, Range: [{stats['min']:.2f}, {stats['max']:.2f}]"
                    elements.append(Paragraph(detail, body_style))
            
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(PageBreak())
        
        # Visualizations
        elements.append(Paragraph("Visual Analysis", heading_style))
        for viz in visualizations:
            if viz.type == "png":
                try:
                    elements.append(Paragraph(viz.name, styles['Heading3']))
                    elements.append(Paragraph(viz.description, body_style))
                    
                    img = Image(viz.path, width=6.5*inch, height=4.5*inch, kind='proportional')
                    elements.append(img)
                    elements.append(Spacer(1, 0.2*inch))
                except Exception as e:
                    logger.warning(f"Failed to add image {viz.path}: {e}")
        
        # Build PDF
        try:
            doc.build(elements)
            logger.info(f"PDF report generated: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    def generate_html_report(
        self,
        dataset_info: Dict[str, Any],
        column_stats: List[Dict[str, Any]],
        correlations: Dict[str, Any],
        outliers: List[Dict[str, Any]],
        data_quality: Dict[str, Any],
        insights: List[LLMInsight],
        visualizations: List[VisualizationData]
    ) -> str:
        """Generate interactive HTML report"""
        
        filepath = self.report_dir / f"report_{self.analysis_id}.html"
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoInsight Report - {{ analysis_id }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        h2 {
            color: #667eea;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        h3 {
            color: #764ba2;
            margin-top: 25px;
            margin-bottom: 15px;
        }
        .metadata {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .metadata-item {
            padding: 10px;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #667eea;
        }
        .metadata-label {
            font-weight: bold;
            color: #667eea;
            font-size: 0.9em;
        }
        .metadata-value {
            font-size: 1.2em;
            margin-top: 5px;
        }
        .insight-section {
            background: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 5px solid #667eea;
        }
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .stats-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .stats-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .stats-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        .visualization {
            margin: 30px 0;
            text-align: center;
        }
        .visualization img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .viz-description {
            font-style: italic;
            color: #666;
            margin-top: 10px;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin: 2px;
        }
        .badge-high { background: #d4edda; color: #155724; }
        .badge-medium { background: #fff3cd; color: #856404; }
        .badge-low { background: #f8d7da; color: #721c24; }
        footer {
            text-align: center;
            padding: 20px;
            margin-top: 40px;
            color: #666;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 AutoInsight</h1>
            <p style="font-size: 1.2em;">Automated Data Analysis Report</p>
        </header>
        
        <div class="metadata">
            <div class="metadata-item">
                <div class="metadata-label">Report ID</div>
                <div class="metadata-value">{{ analysis_id }}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Generated</div>
                <div class="metadata-value">{{ timestamp }}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Dataset Size</div>
                <div class="metadata-value">{{ dataset_info.rows|format_number }} × {{ dataset_info.columns }}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Data Quality</div>
                <div class="metadata-value">{{ "%.1f"|format(data_quality.completeness_percentage) }}%</div>
            </div>
        </div>
        
        {% for insight in insights %}
        <div class="insight-section">
            <h2>{{ insight.section }}</h2>
            <div>{{ insight.content|safe }}</div>
            {% if insight.confidence %}
            <p style="margin-top: 10px;">
                <span class="badge badge-{{ insight.confidence }}">Confidence: {{ insight.confidence }}</span>
            </p>
            {% endif %}
        </div>
        {% endfor %}
        
        <h2>📊 Data Quality Metrics</h2>
        <table class="stats-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Total Rows</td><td>{{ data_quality.total_rows|format_number }}</td></tr>
                <tr><td>Total Columns</td><td>{{ data_quality.total_columns }}</td></tr>
                <tr><td>Missing Cells</td><td>{{ data_quality.missing_cells|format_number }}</td></tr>
                <tr><td>Completeness</td><td>{{ "%.2f"|format(data_quality.completeness_percentage) }}%</td></tr>
                <tr><td>Duplicate Rows</td><td>{{ data_quality.duplicate_rows|format_number }}</td></tr>
                <tr><td>Memory Usage</td><td>{{ "%.2f"|format(data_quality.memory_usage_mb) }} MB</td></tr>
            </tbody>
        </table>
        
        <h2>📈 Visual Analysis</h2>
        {% for viz in visualizations %}
        {% if viz.type == 'png' %}
        <div class="visualization">
            <h3>{{ viz.name }}</h3>
            <img src="visualizations/{{ viz.path|basename }}" alt="{{ viz.name }}">
            <p class="viz-description">{{ viz.description }}</p>
        </div>
        {% endif %}
        {% endfor %}
        
        {% if visualizations|selectattr('type', 'equalto', 'html')|list %}
        <h2>🎯 Interactive Dashboards</h2>
        {% for viz in visualizations %}
        {% if viz.type == 'html' %}
        <div class="visualization">
            <h3>{{ viz.name }}</h3>
            <p class="viz-description">{{ viz.description }}</p>
            <p><a href="visualizations/{{ viz.path|basename }}" target="_blank" style="color: #667eea; font-weight: bold;">Open Interactive Dashboard →</a></p>
        </div>
        {% endif %}
        {% endfor %}
        {% endif %}
        
        <footer>
            <p>Generated by <strong>AutoInsight</strong> - AI-Powered Data Analytics</p>
            <p style="font-size: 0.9em; margin-top: 10px;">This report was automatically generated using advanced statistical analysis and AI insights.</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # Prepare template
        template = Template(template_str)
        
        # Format insights content as HTML
        formatted_insights = []
        for insight in insights:
            content_html = insight.content.replace('\n\n', '</p><p>').replace('\n', '<br>')
            content_html = f'<p>{content_html}</p>'
            formatted_insights.append({
                'section': insight.section,
                'content': content_html,
                'confidence': insight.confidence
            })
        
        # Render HTML
        html_content = template.render(
            analysis_id=self.analysis_id,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            dataset_info=dataset_info,
            data_quality=data_quality,
            insights=formatted_insights,
            visualizations=visualizations,
            format_number=lambda x: f"{x:,}",
            basename=lambda x: Path(x).name
        )
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filepath}")
        return str(filepath)