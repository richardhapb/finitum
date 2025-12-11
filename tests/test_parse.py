from datetime import datetime
from parsers.expense import Expense
from parsers.transference import Transference
from parsers.base import Currency, ExpenseCategory
from email_service.manager import Message

remitent = "test@test.com"
subject = "this is a test"
time_obj = datetime(year=2025, month=9, day=12, hour=12, minute=30)


def test_amount_data_cc():
    usd_expense = """
Banco de Chile Richard Hector Alexander Pe a Bonifaz: Te informamos que se ha realizado
una compra por US$20,88 con Tarjeta de Crédito ****2662 en APPLE.COM BILL CUPERTINO US
el 26/07/2025 20:23. Revisa Saldos y Movimientos en App Mi Banco o Banco en Línea. Más
información 60‍0 63‍7 37‍37. Sigue estos consejos para evitar fraudes Nunca te
llamaremos solicitando tus claves o información personal. Nunca hagas click en links ni
descargues archivos adjuntos de correos sospechosos. Ingresa a la página del Banco
digitando la dirección en la barra de tu navegador. Realiza todo de forma ágil y simple
usando nuestras aplicaciones* Mi Banco ‍Mi Pass Mi Inversión Encuéntranos
bancochile‎.‍cl @‍AyudaBancoChile @‍Bancodechile Banca Telefónica 60‍0 63‍7
37‍37 * Por seguridad, descarga las aplicaciones solo en las tiendas Google Play y App
Store. Las Apps no están disponibles para teléfonos desbloqueados (Jailbreak o
Rooteado). Este mensaje ha sido enviado a 'richard.penab@gmail.com' con información
exclusiva para clientes del banco. Banco de Chile. Casa Matriz: Ahumada 251, Santiago de
Chile. Infórmese sobre la garantía estatal de los depósitos en su banco o en
www‎.‍cmfchile‎.‍cl ©. Todos los derechos reservados. Comprometidos por un medio
ambiente mejor, prefiera los medios digitales al papel impreso.
        """.replace("\n", "")

    clp_expense = """
Banco de Chile Richard Hector Alexander Pe a Bonifaz: Te informamos que se ha realizado
una compra por $38.844 con cargo a Cuenta ****7204 en STA ISABEL JM CAR el 17/09/2025
08:58. Revisa Saldos y Movimientos en App Mi Banco o Banco en Línea. Más información
60‍0 63‍7 37‍37. Sigue estos consejos para evitar fraudes Nunca te llamaremos
solicitando tus claves o información personal. Nunca hagas click en links ni descargues
archivos adjuntos de correos sospechosos. Ingresa a la página del Banco digitando la
dirección en la barra de tu navegador. Realiza todo de forma ágil y simple usando
nuestras aplicaciones* Mi Banco ‍Mi Pass Mi Inversión Encuéntranos
bancochile‎.‍cl @‍AyudaBancoChile @‍Bancodechile Banca Telefónica 60‍0 63‍7
37‍37 * Por seguridad, descarga las aplicaciones solo en las tiendas Google Play y App
Store. Las Apps no están disponibles para teléfonos desbloqueados (Jailbreak o
Rooteado). Este mensaje ha sido enviado a 'richard.penab@gmail.com' con información
exclusiva para clientes del banco. Banco de Chile. Casa Matriz: Ahumada 251, Santiago de
Chile. Infórmese sobre la garantía estatal de los depósitos en su banco o en
www‎.‍cmfchile‎.‍cl ©. Todos los derechos reservados. Comprometidos por un medio
ambiente mejor, prefiera los medios digitales al papel impreso.
        """.replace("\n", "")

    clp_expense_with_number = """
Banco de Chile Richard Hector Alexander Pe a Bonifaz: Te informamos que se ha realizado
una compra por $22.737 con cargo a Cuenta ****7204 en LOCAL 6496-12-12 el 03/09/2025 17:03.
Revisa Saldos y Movimientos en App Mi Banco o Banco en Línea. Más información 60‍0
63‍7 37‍37. Sigue estos consejos para evitar fraudes Nunca te llamaremos solicitando
tus claves o información personal. Nunca hagas click en links ni descargues archivos
adjuntos de correos sospechosos. Ingresa a la página del Banco digitando la dirección
en la barra de tu navegador. Realiza todo de forma ágil y simple usando nuestras
aplicaciones* Mi Banco ‍Mi Pass Mi Inversión Encuéntranos bancochile‎.‍cl
@‍AyudaBancoChile @‍Bancodechile Banca Telefónica 60‍0 63‍7 37‍37 * Por
seguridad, descarga las aplicaciones solo en las tiendas Google Play y App Store. Las
Apps no están disponibles para teléfonos desbloqueados (Jailbreak o Rooteado). Este
mensaje ha sido enviado a 'richard.penab@gmail.com' con información exclusiva para
clientes del banco. Banco de Chile. Casa Matriz: Ahumada 251, Santiago de Chile.
Infórmese sobre la garantía estatal de los depósitos en su banco o en
www‎.‍cmfchile‎.‍cl ©. Todos los derechos reservados. Comprometidos por un medio
ambiente mejor, prefiera los medios digitales al papel impreso.
        """.replace("\n", "")

    msg_usd = Message(remitent, subject, time_obj, usd_expense)

    expense = Expense.get_expense(msg_usd)
    assert expense.value == 20.88
    assert expense.currency == Currency.USD
    assert expense.commerce == "APPLE.COM BILL CUPERTINO US"
    assert expense.category == ExpenseCategory.ONLINE, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj

    msg_clp_num = Message(remitent, subject, time_obj, clp_expense_with_number)

    expense = Expense.get_expense(msg_clp_num)
    assert expense.value == 22737.0
    assert expense.currency == Currency.CLP
    assert expense.commerce == "LOCAL 6496-12-12"
    assert expense.category == ExpenseCategory.GENERAL, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj

    msg_clp = Message(remitent, subject, time_obj, clp_expense)

    expense = Expense.get_expense(msg_clp)
    assert expense.value == 38844.0
    assert expense.commerce == "STA ISABEL JM CAR"
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.FOOD, f"Invalid category for {expense.commerce}"
    assert expense.date == time_obj


def test_parse_data_giro():
    data = """
Banco de Chile Richard Hector Alexander Pe a Bonifaz: Te informamos que se ha realizado
un giro en Cajero por $20.000 con cargo a Cuenta ****7204 el 24/08/2025 11:54. Revisa
Saldos y Movimientos en App Mi Banco o Banco en Línea. Más información 60‍0 63‍7
37‍37. Sigue estos consejos para evitar fraudes Nunca te llamaremos solicitando tus
claves o información personal. Nunca hagas click en links ni descargues archivos
adjuntos de correos sospechosos. Ingresa a la página del Banco digitando la dirección
en la barra de tu navegador. Realiza todo de forma ágil y simple usando nuestras
aplicaciones* Mi Banco ‍Mi Pass Mi Inversión Encuéntranos bancochile‎.‍cl
@‍AyudaBancoChile @‍Bancodechile Banca Telefónica 60‍0 63‍7 37‍37 * Por
seguridad, descarga las aplicaciones solo en las tiendas Google Play y App Store. Las
Apps no están disponibles para teléfonos desbloqueados (Jailbreak o Rooteado). Este
mensaje ha sido enviado a 'richard.penab@gmail.com' con información exclusiva para
clientes del banco. Banco de Chile. Casa Matriz: Ahumada 251, Santiago de Chile.
Infórmese sobre la garantía estatal de los depósitos en su banco o en
www‎.‍cmfchile‎.‍cl ©. Todos los derechos reservados. Comprometidos por un medio
ambiente mejor, prefiera los medios digitales al papel impreso.
            """.replace("\n", "")

    msg = Message(remitent, subject, time_obj, data)
    expense = Expense.get_expense(msg)
    assert expense.value == 20000.0
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.GENERAL
    assert expense.date == time_obj


def test_parse_transference():
    data = """
Banco de Chile | Mi Banco Comprobante de Transferencia a terceros Estimado(a): Richard
Hector Alexander Peña Te informamos que has realizado una Transferencia a terceros en
forma exitosa con el siguiente detalle: Origen Tipo de Cuenta Cuenta Corriente Nº de
Cuenta 00-034-01672-04 Destino Nombre y Apellido Some Person Rut 92019212-3 Tipo de
Cuenta Cuenta Vista Nº de Cuenta 00-002-31471-69 Banco Banco Estado Email Monto $6.000
Mensaje Fecha y Hora: lunes 15 de septiembre de 2025 23:21 Transacción
TEFMBCO2509152321121206234900 Si tienes dudas o consultas, puedes llamar a nuestra Banca
Telefónica o también, dirigirte a cualquiera de nuestras sucursales. bancochile.cl
@AyudaBancoChile @bancodechile 600 637 37 37 Banca Telefónica ES CLAVE NO DAR TUS CLAVES
Por seguridad, este cuerpo no contiene enlaces al sítio Web de Banco de Chile Importante
• Es clave no dar tu claves. • Nunca entregar claves, información financiera o datos
personales a nadie. • Ingresar a la página del Banco digitando la dirección en la
barra del navegador. • Nunca descargar archivos adjuntos de remitentes desconocidos.
• Solo seguir nuestras cuentas oficiales certificadas en redes sociales (fijarse en el
check junto al nombre de la cuenta). • Mantener actualizado el antivirus. • En caso
de detectar actividad sospechosa, contactarnos a través de nuestros canales oficiales de
ayuda. • Información de cómo evitar ser víctima de un fraude en nuestra página web.
Banco de Chile. Casa Matriz: Ahumada 251, Santiago de Chile. Infórmese sobre la
garantía estatal de los depósitos en su banco o en www.cmfchile.cl. © 2025. Todos los
derechos reservados. Comprometidos por un medio ambiente mejor, prefiera los medios
digitales al papel impreso.
        """.replace("\n", "")

    msg = Message(remitent, subject, time_obj, data)

    transference = Transference.get_transference(msg)
    assert transference.value == 6000.0
    assert transference.currency == Currency.CLP
    assert transference.recipient == "Some Person"
    assert transference.category == ExpenseCategory.GENERAL
    assert transference.date == time_obj


def test_parse_app_transference():
    data = """
Mailing Estimado(a) Richard Hector Alexander Peña Bonifaz Le informamos que usted ha
efectuado una transferencia de fondos a Medio De Pago Fintoc, el día 08 de septiembre de
2025, desde su Cuenta Corriente 340167204. El detalle puede revisarlo a continuación
DESDE HOY PUEDES AUTORIZAR TUS TRANSFERENCIAS EN TU CELULAR CON LA APLICACION MI PASS EN
VEZ DE DIGIPASS Y AHORRA TIEMPO.DESCARGA MI PASS DESDE GOOGLE PLAY O APPLE STORE. Datos
del Destinatario Nombre Medio De Pago Fintoc Rut 77.143.385-5 Cuenta 922358017 Banco
Banco Security Mail transferencias@fintoc.com Datos de la Transferencia Fecha 08/09/2025
Cuenta 340167204 Monto $10.000 ID TEF_IPE2509080811121093527740 Mensaje
1FIN-pi_32PktX3C0lCZPSdGoAvnaro8MKA Por tu seguridad, este mensaje no tiene enlace al
sitio web de Banco de Chile, además: Nunca te pediremos ingresar a un sitio web desde un
correo Nunca te pediremos ingresar tu clave Digipass antes del ingreso a tu Banco en
Línea, ni al inicio de tu sesión Nunca te llamaremos ni pediremos por SMS tus claves,
datos personales o tu clave Digipass Nunca hagas click en un link desde un correo porque
puede llevarte a un sitio falso Verifica siempre que la URL del Banco en Línea comience
con https://(en vez de http://) No hagas click en un link de resultado de búsqueda.
Hasta un buscador puede no ser seguro. Infórmese sobre la garantía estatal de los
depósitos en su banco o en www.sbif.cl © 2019 Banco de Chile. Todos los Derechos Reservados.
        """.replace("\n", "")

    msg = Message(remitent, subject, time_obj, data)

    transference = Transference.get_transference(msg)
    assert transference.value == 10000.0
    assert transference.currency == Currency.CLP
    assert transference.recipient == "Medio De Pago Fintoc"
    assert transference.category == ExpenseCategory.FAMILY
    assert transference.date == time_obj
