from PIL import ImageFont
from barcode.writer import mm2px, ImageWriter, FONT


class BarcodeImageWriter(ImageWriter):
    def calculate_size(self, modules_per_line, number_of_lines, dpi=300):
        width = 2 * self.quiet_zone + modules_per_line * self.module_width
        height = 1.0 + self.module_height * number_of_lines
        if self.text:
            height += 2 * self.text_distance + self.font_size * 0.09
        self.width = width
        self.height = height
        self.size = int(mm2px(width, dpi)), int(mm2px(height, dpi))
        return self.size

    def _paint_text(self, xpos, ypos):
        xpos = self.width/2
        letter_width = self.font_size * 0.78  # letter size = 23d x 18d -> ratio = 0.78
        text_width = len(self.text) * letter_width * 0.065 * (float(300) / self.dpi)
        xpos -= text_width/2
        pos = (mm2px(xpos, self.dpi), mm2px(ypos, self.dpi))
        font = ImageFont.truetype(FONT, self.font_size)
        self._draw.text(pos, self.text, font=font, fill=self.foreground)
