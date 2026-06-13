from datetime import date
from decimal import Decimal


_BASE = """
<html>
<head>
  <meta charset="utf-8">
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#fff;border-radius:12px;overflow:hidden;
                      box-shadow:0 4px 16px rgba(0,0,0,.08);">
          <tr>
            <td style="background:#11a691;padding:24px 32px;">
              <h1 style="margin:0;color:#fff;font-size:22px;">Centro de Actividades</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              {content}
            </td>
          </tr>
          <tr>
            <td style="background:#f9f9f9;padding:16px 32px;
                       border-top:1px solid #eee;text-align:center;">
              <p style="margin:0;color:#aaa;font-size:12px;">
                Si no esperabas este mensaje, podés ignorarlo.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def _wrap(content: str) -> str:
    return _BASE.format(content=content)


def welcome(first_name: str) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Hola, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu cuenta fue creada con éxito en <strong>Centro de Actividades</strong>.
        Ya podés explorar y reservar todas nuestras actividades disponibles.
      </p>
      <p style="margin-top:28px;">
        <a href="#"
           style="background:#11a691;color:#fff;padding:12px 24px;
                  border-radius:8px;text-decoration:none;font-weight:bold;">
          Ver actividades
        </a>
      </p>
    """
    return _wrap(content)


def password_reset(reset_url: str) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">Recuperá tu contraseña</h2>
      <p style="color:#444;line-height:1.6;">
        Recibimos una solicitud para restablecer la contraseña de tu cuenta en
        <strong>Centro de Actividades</strong>.
        Hacé clic en el botón para crear una nueva contraseña.
        El enlace es válido por <strong>15 minutos</strong> y de un solo uso.
      </p>
      <p style="margin-top:28px;">
        <a href="{reset_url}"
           style="background:#11a691;color:#fff;padding:12px 24px;
                  border-radius:8px;text-decoration:none;font-weight:bold;">
          Restablecer contraseña
        </a>
      </p>
      <p style="color:#aaa;font-size:12px;margin-top:24px;">
        Si no solicitaste este cambio, podés ignorar este mensaje. Tu contraseña no será modificada.
      </p>
    """
    return _wrap(content)


def subscription_payment_confirmed(
    first_name: str,
    activity_name: str,
    turno_description: str,
    amount: Decimal,
    payment_id: str,
    original_amount: Decimal = Decimal(0),
    discount_full_classes: Decimal = Decimal(0),
) -> str:
    if payment_id == "free":
        payment_row = ""
        amount_label = "Sin costo adicional"
        amount_value = "$ 0,00"
    else:
        payment_row = f"""
        <tr>
          <td style="color:#666;font-size:13px;">N° transacción MP</td>
          <td style="color:#888;font-size:13px;font-family:monospace;">{payment_id}</td>
        </tr>"""
        amount_label = "Total abonado"
        amount_value = f"$ {amount:,.2f}"

    discount_single = original_amount - amount - discount_full_classes
    precio_base = original_amount + discount_full_classes

    price_rows = ""
    if discount_full_classes > 0 or discount_single > 0:
        price_rows += f"""
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Precio mensual</td>
          <td style="color:#222;">$ {precio_base:,.2f}</td>
        </tr>"""
        if discount_full_classes > 0:
            price_rows += f"""
        <tr>
          <td style="color:#e53935;font-size:13px;">Descuento por clase con cupo lleno</td>
          <td style="color:#e53935;">- $ {discount_full_classes:,.2f}</td>
        </tr>"""
        if discount_single > 0:
            price_rows += f"""
        <tr style="background:#f0faf8;">
          <td style="color:#e53935;font-size:13px;">Descuento por clases individuales ya abonadas</td>
          <td style="color:#e53935;">- $ {discount_single:,.2f}</td>
        </tr>"""

    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Suscripción confirmada, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu suscripción quedó activa. A partir de ahora tenés el cupo reservado en cada clase del turno.
        El costo se renueva mes a mes según las clases del período.
      </p>
      <table width="100%" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;margin:20px 0;">
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Actividad</td>
          <td style="color:#222;font-weight:bold;">{activity_name}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Turno</td>
          <td style="color:#222;">{turno_description}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Tipo</td>
          <td style="color:#222;">Suscripción mensual</td>
        </tr>{price_rows}
        <tr>
          <td style="color:#666;font-size:13px;"><strong>{amount_label}</strong></td>
          <td style="color:#222;font-weight:bold;">{amount_value}</td>
        </tr>{payment_row}
      </table>
      <p style="color:#444;line-height:1.6;">
        ¡Te esperamos! Si tenés alguna consulta, contactanos por nuestros canales habituales.
      </p>
    """
    return _wrap(content)


_MONTHS = ["enero","febrero","marzo","abril","mayo","junio",
           "julio","agosto","septiembre","octubre","noviembre","diciembre"]
_DAYS = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]


def _fmt_date(d: date) -> str:
    return f"{_DAYS[d.weekday()].capitalize()} {d.day} de {_MONTHS[d.month - 1]}"


def _dates_html(clase_dates: list[date]) -> str:
    if not clase_dates:
        return ""
    label = "Fecha de la clase" if len(clase_dates) == 1 else "Fechas de las clases"
    dates_str = "<br>".join(_fmt_date(d) for d in clase_dates)
    return f"""
        <tr>
          <td style="color:#666;font-size:13px;">{label}</td>
          <td style="color:#222;">{dates_str}</td>
        </tr>"""


def single_payment_confirmed(
    first_name: str,
    activity_name: str,
    turno_description: str,
    num_classes: int,
    class_price: Decimal,
    amount: Decimal,
    payment_id: str,
    clase_dates: list[date] | None = None,
) -> str:
    clases_label = "clase" if num_classes == 1 else "clases"
    dates_row = _dates_html(clase_dates or [])
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Inscripción confirmada, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu reserva de {num_classes} {clases_label} individual{"" if num_classes == 1 else "es"} quedó confirmada.
      </p>
      <table width="100%" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;margin:20px 0;">
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Actividad</td>
          <td style="color:#222;font-weight:bold;">{activity_name}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Turno</td>
          <td style="color:#222;">{turno_description}</td>
        </tr>{dates_row}
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Clases reservadas</td>
          <td style="color:#222;">{num_classes}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Precio por clase</td>
          <td style="color:#222;">$ {class_price:,.2f}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Total abonado</td>
          <td style="color:#222;font-weight:bold;">$ {amount:,.2f}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">N° transacción MP</td>
          <td style="color:#888;font-size:13px;font-family:monospace;">{payment_id}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        ¡Te esperamos! Si tenés alguna consulta, contactanos por nuestros canales habituales.
      </p>
    """
    return _wrap(content)


def deposit_confirmed(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_dates: list[date],
    deposit_amount: Decimal,
    balance_amount: Decimal,
    payment_id: str,
) -> str:
    dates_row = _dates_html(clase_dates)
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Seña confirmada, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu seña del 30% fue registrada. Tu lugar está reservado.
      </p>
      <table width="100%" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;margin:20px 0;">
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Actividad</td>
          <td style="color:#222;font-weight:bold;">{activity_name}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Turno</td>
          <td style="color:#222;">{turno_description}</td>
        </tr>{dates_row}
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Seña abonada (30%)</td>
          <td style="color:#222;font-weight:bold;">$ {deposit_amount:,.2f}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Saldo pendiente (70%)</td>
          <td style="color:#222;font-weight:bold;">$ {balance_amount:,.2f}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">N° transacción MP</td>
          <td style="color:#888;font-size:13px;font-family:monospace;">{payment_id}</td>
        </tr>
      </table>
      <p style="color:#e65100;font-weight:bold;line-height:1.6;">
        ⚠ Debés abonar el saldo restante al menos 1 hora antes del inicio de la clase para poder participar.
        Si no completás el pago, perderás la seña abonada.
      </p>
      <p style="color:#444;line-height:1.6;">
        Podés completar el pago desde "Mis actividades". ¡Te esperamos!
      </p>
    """
    return _wrap(content)


def balance_confirmed(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_dates: list[date],
    class_price: Decimal,
    deposit_amount: Decimal,
    balance_amount: Decimal,
    payment_id: str,
) -> str:
    dates_row = _dates_html(clase_dates)
    total = deposit_amount + balance_amount
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Pago completado, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu inscripción a la clase individual está confirmada.
      </p>
      <table width="100%" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;margin:20px 0;">
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Actividad</td>
          <td style="color:#222;font-weight:bold;">{activity_name}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Turno</td>
          <td style="color:#222;">{turno_description}</td>
        </tr>{dates_row}
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Precio por clase</td>
          <td style="color:#222;">$ {class_price:,.2f}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Seña abonada (30%)</td>
          <td style="color:#222;">$ {deposit_amount:,.2f}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Saldo abonado (70%)</td>
          <td style="color:#222;">$ {balance_amount:,.2f}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Total</td>
          <td style="color:#222;font-weight:bold;">$ {total:,.2f}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">N° transacción MP (saldo)</td>
          <td style="color:#888;font-size:13px;font-family:monospace;">{payment_id}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        ¡Te esperamos! Si tenés alguna consulta, contactanos por nuestros canales habituales.
      </p>
    """
    return _wrap(content)
