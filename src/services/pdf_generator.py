"""PDF generator service using WeasyPrint."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.models.report_data import ReportData


class PdfGenerator:
    """Generates PDF reports from HTML templates using WeasyPrint."""

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the PDF generator.

        Args:
            template_dir: Directory containing templates. Defaults to templates/.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates"
        self._template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )

    def generate(self, report_data: ReportData, output_path: Path) -> Path:
        """Generate PDF from report data.

        Args:
            report_data: Aggregated report data to render.
            output_path: Path where PDF will be saved.

        Returns:
            Path to the generated PDF file.
        """
        html_content = self._render_html(report_data)
        self._compile_pdf(html_content, output_path)
        return output_path

    def _render_html(self, report_data: ReportData) -> str:
        """Render Jinja2 HTML template with report data.

        Args:
            report_data: Data to render into the template.

        Returns:
            Rendered HTML string.
        """
        template = self._env.get_template("report.html.jinja")
        result: str = template.render(report=report_data)
        return result

    def _compile_pdf(self, html_content: str, output_path: Path) -> None:
        """Compile HTML to PDF using WeasyPrint.

        Args:
            html_content: Rendered HTML string.
            output_path: Path where PDF will be saved.
        """
        from weasyprint import HTML

        output_path.parent.mkdir(parents=True, exist_ok=True)
        css_path = self._template_dir / "report.css"
        stylesheets = [str(css_path)] if css_path.exists() else None
        HTML(string=html_content, base_url=str(self._template_dir)).write_pdf(
            output_path, stylesheets=stylesheets
        )

    def render_html_for_email(self, report_data: ReportData) -> str:
        """Render HTML suitable for email body.

        Args:
            report_data: Data to render into the template.

        Returns:
            Rendered HTML string with inline styles.
        """
        template = self._env.get_template("report.html.jinja")
        result: str = template.render(report=report_data, inline_styles=True)
        return result
