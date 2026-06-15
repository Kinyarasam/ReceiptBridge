#!/usr/bin/env python3
from io import BytesIO
from typing import Tuple, Dict, Any

from numpy import char


class ESCPOSGenerator:
    """Generate ESC/POS commands for receipt printing
    """

    # ESC/POS Commands
    ESC = b'\x1B'
    GS = b'\x1D'

    # Initialize printer
    INIT = ESC + b'@'

    # Text formatting
    BOLD_ON = ESC + b'E' + b'x\01'
    BOLD_OFF = ESC + b'E' + b'x\00'

    # Alignment
    ALIGN_LEFT = ESC + b'a' + b'\x00'
    ALIGN_CENTER = ESC + b'a' + b'\x01'
    ALIGN_RIGHT = ESC + b'a' + b'\x02'

    # Font size
    FONT_NORMAL = ESC + b'!' + b'\x00'
    FONT_DOUBLE_BOTH = ESC + b'!' + b'\x30'

    # Paper cutting
    FULL_CUT = GS + b'V' + b'\x00'

    @classmethod
    def encode_text(cls, text: str, encoding: str = 'cp437') -> bytes:
        """Encode text for ESC/POS printer
        """
        try:
            return text.encode(encoding, errors='replace')
        except:
            return text.encode('ascii', errors='replace')

    @classmethod
    def line(cls, text: str = '') -> bytes:
        """Print a line of text
        """
        if text:
            return cls.encode_text(text + '\n')
        return cls.encode_text('\n')

    @classmethod
    def separator(cls, char: str = '-', length: int = 32) -> bytes:
        """Print a separator line
        """
        return cls.encode_text(char * length + '\n')

    @classmethod
    def double_separator(cls, length: int = 32) -> bytes:
        """Print a double separator line
        """
        return cls.encode_text('=' * length + '\n')

    @classmethod
    def generate_receipt(cls, order_data: Dict[str, Any]) -> bytes:
        """Generate complete ESC/POS receipt
        """
        buffer = BytesIO()

        # Initialize printer
        buffer.write(cls.INIT)

        # Center alignment for header
        buffer.write(cls.ALIGN_CENTER)
        buffer.write(cls.BOLD_ON)
        buffer.write(cls.FONT_DOUBLE_BOTH)
        buffer.write(cls.line("Receipt"))
        buffer.write(cls.FONT_NORMAL)
        buffer.write(cls.BOLD_OFF)
        buffer.write(cls.line())

        # Left alignment for content
        buffer.write(cls.ALIGN_LEFT)

        # Order info
        buffer.write(cls.line(f"Order #: {order_data['order_number']}"))
        buffer.write(cls.line(f"Date: {order_data['created_at']}"))
        buffer.write(cls.line())

        # Customer info
        customer = order_data.get('customer', {})
        if customer:
            name = f"{customer.get('first_name')} {customer.get('last_name')}".strip()
            if name:
                buffer.write(cls.line(f"Customer: {name}"))
            if customer.get('email'):
                buffer.write(cls.line(f"Email: {customer.get('email')}"))
            if customer.get('phone_number'):
                buffer.write(cls.line(f"Phone: {customer.get('phone_number')}"))
            buffer.write(cls.line())

        buffer.write(cls.separator('-'))

        # Items header
        buffer.write(cls.BOLD_ON)
        buffer.write(cls.line(f"{'Item':<20} {'Qty':>4} {'Price':>8}"))
        buffer.write(cls.BOLD_OFF)
        buffer.write(cls.separator('-'))

        # Items
        for item in order_data.get('line_items', []):
            name = item.get('title', 'Unknown')[:20]
            qty = item.get('quantity', 0)
            price = float(item.get('price', 0)) * qty
            buffer.write(cls.line(f"{name:<20} {qty:>4} ${price:>7.2f}"))

        buffer.write(cls.separator('-'))

        # Totals
        subtotal = float(order_data.get('subtotal_price', 0))
        tax = float(order_data.get('total_tax', 0))
        total = float(order_data.get('total_price', 0))

        buffer.write(cls.line(f"{'Subtotal:':<20} ${subtotal:>7.2f}"))
        if tax > 0:
            buffer.write(cls.line(f"{'Tax:':<20} ${tax:>7.2f}"))
        buffer.write(cls.double_separator())
        buffer.write(cls.BOLD_ON)
        buffer.write(cls.line(f"{'TOTAL:':<20} ${total:>7.2f}"))
        buffer.write(cls.BOLD_OFF)

        # Footer
        buffer.write(cls.line())
        buffer.write(cls.ALIGN_CENTER)
        buffer.write(cls.line("Thank you!"))
        buffer.write(cls.line("Visit us again"))
        buffer.write(cls.line())
        buffer.write(cls.line())

        # Cut paper
        buffer.write(cls.FULL_CUT)

        return buffer.getvalue()