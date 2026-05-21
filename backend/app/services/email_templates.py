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


def enrollment_confirmed(
    first_name: str,
    activity_name: str,
    turno_description: str,
    amount: Decimal,
    payment_id: str,
) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Pago confirmado, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu inscripción quedó confirmada. Estos son los detalles:
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
          <td style="color:#666;font-size:13px;">Monto pagado</td>
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


def payment_confirmed(
    first_name: str,
    activity_name: str,
    turno_description: str,
    price: Decimal,
    payment_id: str,
) -> str:
    content = f"""
      <h2 style="color:#11a691;margin-top:0;">¡Pago confirmado, {first_name}!</h2>
      <p style="color:#444;line-height:1.6;">
        Tu inscripción quedó registrada. Estos son los detalles:
      </p>
      <table width="100%" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;margin:20px 0;">
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;border-radius:4px 0 0 4px;">Actividad</td>
          <td style="color:#222;font-weight:bold;">{activity_name}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">Turno</td>
          <td style="color:#222;">{turno_description}</td>
        </tr>
        <tr style="background:#f0faf8;">
          <td style="color:#666;font-size:13px;">Monto pagado</td>
          <td style="color:#222;font-weight:bold;">$ {price:,.2f}</td>
        </tr>
        <tr>
          <td style="color:#666;font-size:13px;">N° comprobante MP</td>
          <td style="color:#888;font-size:13px;font-family:monospace;">{payment_id}</td>
        </tr>
      </table>
      <p style="color:#444;line-height:1.6;margin-top:16px;">
        ¡Te esperamos! Si tenés alguna consulta, contactanos por nuestros canales habituales.
      </p>
    """
    return _wrap(content)
