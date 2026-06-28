from datetime import date, datetime
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


def deposit_refunded(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_start: datetime,
    deposit_amount: Decimal,
) -> str:
    fecha = clase_start.strftime("%-d de %B de %Y")
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">Reembolso de seña confirmado, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        Tu inscripción fue cancelada y tu seña será reembolsada por el centro.
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
          <td style="color:#666;font-size:13px;">Fecha de clase cancelada</td>
          <td style="color:#222;">{fecha}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Monto a reembolsar</td>
          <td style="color:#11a691;font-weight:bold;">$ {deposit_amount:,.2f}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        El centro procesará la devolución a través de los canales de pago habituales.
        Si tenés alguna consulta, contactanos.
      </p>
    """
    return _wrap(content)


def clase_cancelada_suscripcion(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_date: date,
    expires_days: int,
    reason: str,
) -> str:
    fecha = clase_date.strftime("%-d de %B de %Y")
    content = f"""
      <h2 style="color:#e05252;margin-top:0;">Clase cancelada, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        El centro canceló una clase de tu abono mensual. Se generó un crédito
        a tu favor para usar en cualquier actividad del centro dentro de los
        próximos {expires_days} días.
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
          <td style="color:#666;font-size:13px;">Fecha de clase cancelada</td>
          <td style="color:#222;">{fecha}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Crédito generado</td>
          <td style="color:#11a691;font-weight:bold;">1 clase</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Válido por</td>
          <td style="color:#222;">{expires_days} días</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Motivo</td>
          <td style="color:#444;">{reason}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        Podés ver y usar tu crédito al inscribirte en cualquier actividad.
        Lamentamos los inconvenientes.
      </p>
    """
    return _wrap(content)


def clase_cancelada_individual_completo(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_date: date,
    expires_days: int,
    reason: str,
) -> str:
    fecha = clase_date.strftime("%-d de %B de %Y")
    content = f"""
      <h2 style="color:#e05252;margin-top:0;">Clase cancelada, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        El centro canceló una clase que tenías reservada. Se generó un crédito
        a tu favor para usar en cualquier actividad del centro dentro de los próximos {expires_days} días.
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
          <td style="color:#666;font-size:13px;">Fecha de clase cancelada</td>
          <td style="color:#222;">{fecha}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Crédito generado</td>
          <td style="color:#11a691;font-weight:bold;">1 clase</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Válido por</td>
          <td style="color:#222;">{expires_days} días</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Motivo</td>
          <td style="color:#444;">{reason}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        Podés ver y usar tu crédito al inscribirte en cualquier actividad.
        Lamentamos los inconvenientes.
      </p>
    """
    return _wrap(content)


def clase_cancelada_individual_senia(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_date: date,
    senia: Decimal,
    reason: str,
) -> str:
    fecha = clase_date.strftime("%-d de %B de %Y")
    content = f"""
      <h2 style="color:#e05252;margin-top:0;">Clase cancelada, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        El centro canceló una clase que tenías reservada con seña. El centro
        reembolsará el monto abonado por los canales habituales.
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
          <td style="color:#666;font-size:13px;">Fecha de clase cancelada</td>
          <td style="color:#222;">{fecha}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Monto a reembolsar</td>
          <td style="color:#11a691;font-weight:bold;">$ {senia:,.2f}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Motivo</td>
          <td style="color:#444;">{reason}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        Lamentamos los inconvenientes. Si tenés alguna consulta, contactanos.
      </p>
    """
    return _wrap(content)


def turno_baja(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clases_canceladas: int,
    creditos: int,
    senia: Decimal,
    expires_days: int,
    reason: str,
) -> str:
    """Mail-resumen único para un afectado cuando se da de baja un turno entero."""
    if creditos > 0:
        credito_html = f"""
        <tr>
          <td style="color:#666;font-size:13px;">Créditos generados</td>
          <td style="color:#11a691;font-weight:bold;">{creditos} clase{'s' if creditos != 1 else ''}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Válidos por</td>
          <td style="color:#222;">{expires_days} días</td>
        </tr>"""
        cierre = (
            "Podés ver y usar tus créditos al inscribirte en cualquier actividad. "
            "Lamentamos los inconvenientes."
        )
    elif senia and senia > 0:
        credito_html = f"""
        <tr>
          <td style="color:#666;font-size:13px;">Seña a reembolsar</td>
          <td style="color:#11a691;font-weight:bold;">$ {senia:,.2f}</td>
        </tr>"""
        cierre = (
            "Sobre tu seña, contactanos para gestionar la devolución. "
            "Lamentamos los inconvenientes."
        )
    else:
        credito_html = ""
        cierre = (
            "No se generaron créditos porque no había clases abonadas pendientes de dictarse. "
            "Lamentamos los inconvenientes."
        )

    content = f"""
      <h2 style="color:#e05252;margin-top:0;">Se dio de baja un turno, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        El centro dio de baja un turno en el que estabas inscripto/a y ya no se dictará.
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
          <td style="color:#666;font-size:13px;">Clases canceladas</td>
          <td style="color:#222;">{clases_canceladas}</td>
        </tr>{credito_html}
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Motivo</td>
          <td style="color:#444;">{reason}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">{cierre}</p>
    """
    return _wrap(content)


def cambio_horario_turno(
    first_name: str,
    activity_name: str,
    turno_description: str,
    dias_str: str,
    horario_str: str,
) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">Tu turno cambió, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        El centro actualizó los días u horario de un turno en el que estás
        inscripto. Tu lugar sigue reservado; solo cambió cuándo se dicta.
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
          <td style="color:#666;font-size:13px;">Nuevos días</td>
          <td style="color:#222;">{dias_str}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Nuevo horario</td>
          <td style="color:#222;">{horario_str}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        Si el nuevo horario no te sirve, podés gestionar tu baja desde tu cuenta.
        Cualquier duda, contactanos.
      </p>
    """
    return _wrap(content)


def cambio_horario_clase(
    first_name: str,
    activity_name: str,
    turno_description: str,
    clase_date: date,
    horario_str: str,
) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">Cambió el horario de tu clase, {first_name}</h2>
      <p style="color:#444;line-height:1.6;">
        El centro modificó una clase puntual en la que estás inscripto. Tu lugar
        sigue reservado; solo cambió cuándo se dicta esta clase. El resto del turno
        no se modifica.
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
          <td style="color:#666;font-size:13px;">Nueva fecha</td>
          <td style="color:#222;">{_fmt_date(clase_date)}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Nuevo horario</td>
          <td style="color:#222;">{horario_str}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;">
        Si el nuevo horario no te sirve, contactanos. ¡Te esperamos!
      </p>
    """
    return _wrap(content)


def waitlist_promoted(
    first_name: str,
    activity_name: str,
    turno_description: str,
    amount: float,
    ttl_minutes: int = 1440,
) -> str:
    if ttl_minutes >= 60:
        hours = ttl_minutes // 60
        ttl_label = f"{hours} {'hora' if hours == 1 else 'horas'}"
    else:
        ttl_label = f"{ttl_minutes} {'minuto' if ttl_minutes == 1 else 'minutos'}"
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">&#x1F389; Hay un lugar para vos, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Se liberó un cupo en <strong>{activity_name}</strong> ({turno_description}).
        Como estabas en la lista de espera, te reservamos el lugar.
      </p>
      <table width="100%" cellpadding="8" style="border-collapse:collapse;margin:20px 0;">
        <tr>
          <td style="color:#666;font-size:13px;width:45%;">Actividad</td>
          <td style="color:#222;font-weight:bold;">{activity_name}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Turno</td>
          <td style="color:#222;">{turno_description}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Monto a pagar</td>
          <td style="color:#11a691;font-weight:bold;">$ {amount:,.2f}</td>
        </tr>
      </table>
      <p style="color:#e65100;font-size:13px;">
        Tenés <strong>{ttl_label}</strong> para completar el pago.
        Si no pagás a tiempo, el lugar pasará al siguiente en la lista.
      </p>
      <p style="color:#444;line-height:1.6;">
        Para completar el pago ingresá a tu cuenta y dirigite a la sección
        <strong>Suscripciones</strong>, donde vas a encontrar el cargo pendiente.
      </p>
    """
    return _wrap(content)


def employee_welcome(first_name: str, set_password_url: str) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Bienvenido/a al equipo, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Se creó tu cuenta de empleado en <strong>Centro de Actividades</strong>.
        Para acceder al sistema por primera vez, tenés que establecer tu contraseña
        haciendo clic en el botón de abajo.
      </p>
      <p style="color:#888;font-size:13px;">
        El enlace es válido por <strong>24 horas</strong> y de un solo uso.
      </p>
      <p style="margin-top:28px;">
        <a href="{set_password_url}"
           style="background:#11a691;color:#fff;padding:12px 24px;
                  border-radius:8px;text-decoration:none;font-weight:bold;">
          Establecer contraseña
        </a>
      </p>
      <p style="color:#aaa;font-size:12px;margin-top:24px;">
        Si no esperabas este mensaje, podés ignorarlo.
      </p>
    """
    return _wrap(content)

