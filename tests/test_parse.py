from datetime import datetime, timezone
import json
from main import clean_body
from parse import Currency, ExpenseCategory, Expense, Transference, TZ


def test_email_parsing():
    text = b"""{\n    "subject": "Cargo en Cuenta",\n     "time": "2025-09-12T20:24:24.000Z",
\n     "content": " fraudes\n\n[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca
te llamaremos solicitando tus claves o informaci\xc3\xb3n
personal.\n\n[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca
hagas click en links ni descargues archivos adjuntos de correos
sospechosos.\n\n[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png]
Ingresa a la p\xc3\xa1gina del Banco digitando la direcci\xc3\xb3n en la barra
de tu navegador.\n\nRealiza todo de forma \xc3\xa1gil y simple usando nuestras
aplicaciones*\n\n[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]\n\nMi
Banco\n\n[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\n\n\xe2\x80\x8dMi
Pass\n\n[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]\n\nMi
Inversi\xc3\xb3n\n\n\n\nEncu\xc3\xa9ntranos\n\n[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
bancochile\xe2\x80\x8e.\xe2\x80\x8dcl\n\n[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
@\xe2\x80\x8dAyudaBancoChile\n\n[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
@\xe2\x80\x8dBancodechile\n\n[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png]
Banca Telef\xc3\xb3nica\n\n60\xe2\x80\x8d0 63\xe2\x80\x8d7
37\xe2\x80\x8d37\n\n* Por seguridad, descarga las aplicaciones solo en las
tiendas Google Play y App Store. Las Apps no est\xc3\xa1n disponibles para
tel\xc3\xa9fonos desbloqueados (Jailbreak o Rooteado).\n\nEste mensaje ha sido
enviado a \'richard.penab@gmail.com\' con informaci\xc3\xb3n exclusiva para
clientes del banco. Banco de Chile. Casa Matriz: Ahumada 251, Santiago de
Chile.\nInf\xc3\xb3rmese sobre la garant\xc3\xada estatal de los
dep\xc3\xb3sitos en su banco o en
www\xe2\x80\x8e.\xe2\x80\x8dcmfchile\xe2\x80\x8e.\xe2\x80\x8dcl
\xc2\xa9.\nTodos los derechos reservados.\nHoja
[http://contentz.mkt8988.com/lp/14944/107981/hoja.png] Comprometidos por un
medio ambiente mejor, prefiera los medios digitales al papel impreso.
[http://bancochile.cl/img/PS76JRn/pIolTcsauGpvWr527XL/belEcd0GnH+ooDQ=ttp://bancochile.cl/img/${id}]"\n}"""

    data = json.loads(clean_body(text))

    assert isinstance(data, dict)


def test_amount_data_cc():
    parsed_usd = {
        "subject": "Compra con Terjeta de Crédito",
        "time": "2025-09-12T20:24:24.000Z",
        "content": """
        [http://contentz.mkt8988.com/lp/14944/107881/BCH_nuevo.png] Richard Hector Alexander Pe a Bonifaz:Te
        informamos que se ha realizado una compra por US$15,20 con Tarjeta de Crédito ****2662 en Upwork
        -845399262ConnectsDublin IE el 12/09/2025 17:24.Revisa Saldos y Movimientos en App Mi Banco o Banco en
        Línea.Más información 60\u200d0 63\u200d7
        37\u200d37.[http://contentz.mkt8988.com/lp/14944/107981/aleta_BCH.png]Sigue estos consejos para evitar
        fraudes[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca te llamaremos solicitando tus
        claves o información personal.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca hagas click
        en links ni descargues archivos adjuntos de correos
        sospechosos.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Ingresa a la página del Banco
        digitando la dirección en la barra de tu navegador.Realiza todo de forma ágil y simple usando nuestras
        aplicaciones*[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]Mi
        Banco[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\u200dMi
        Pass[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]Mi
        InversiónEncuéntranos[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
        bancochile\u200e.\u200dcl[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
        @\u200dAyudaBancoChile[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
        @\u200dBancodechile[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png] Banca Telefónica60\u200d0
        63\u200d7 37\u200d37* Por seguridad, descarga las aplicaciones solo en las tiendas Google Play y App Store.
        Las Apps no están disponibles para teléfonos desbloqueados (Jailbreak o Rooteado).Este mensaje ha sido
        enviado a 'richard.penab@gmail.com' con información exclusiva para clientes del banco. Banco de Chile. Casa
        Matriz: Ahumada 251, Santiago de Chile.Infórmese sobre la garantía estatal de los depósitos en su banco o
        en www\u200e.\u200dcmfchile\u200e.\u200dcl ©.Todos los derechos reservados.Hoja
        [http://contentz.mkt8988.com/lp/14944/107981/hoja.png] Comprometidos por un medio ambiente mejor, prefiera
        los medios digitales al papel impreso.
        [http://bancochile.cl/img/PS76JRn/pIolTcsauGpvWl9Atyie7MwN8CHjl3MRFXk=ttp://bancochile.cl/img/${id}]
        """.replace("\n", ""),
    }

    parsed_clp = {
        "subject": "Compra con Terjeta de Crédito",
        "time": "2025-09-12T20:24:24.000Z",
        "content": """
        [http://contentz.mkt8988.com/lp/14944/107881/BCH_nuevo.png] Richard Hector Alexander Pe a Bonifaz:Te
        informamos que se ha realizado una compra por $7.050 con Tarjeta de Crédito ****2662 en Upwork
        -845399262ConnectsDublin IE el 09/09/2025 17:24.Revisa Saldos y Movimientos en App Mi Banco o Banco en
        Línea.Más información 60\u200d0 63\u200d7
        37\u200d37.[http://contentz.mkt8988.com/lp/14944/107981/aleta_BCH.png]Sigue estos consejos para evitar
        fraudes[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca te llamaremos solicitando tus
        claves o información personal.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca hagas click
        en links ni descargues archivos adjuntos de correos
        sospechosos.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Ingresa a la página del Banco
        digitando la dirección en la barra de tu navegador.Realiza todo de forma ágil y simple usando nuestras
        aplicaciones*[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]Mi
        Banco[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\u200dMi
        Pass[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]Mi
        InversiónEncuéntranos[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
        bancochile\u200e.\u200dcl[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
        @\u200dAyudaBancoChile[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
        @\u200dBancodechile[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png] Banca Telefónica60\u200d0
        63\u200d7 37\u200d37* Por seguridad, descarga las aplicaciones solo en las tiendas Google Play y App Store.
        Las Apps no están disponibles para teléfonos desbloqueados (Jailbreak o Rooteado).Este mensaje ha sido
        enviado a 'richard.penab@gmail.com' con información exclusiva para clientes del banco. Banco de Chile. Casa
        Matriz: Ahumada 251, Santiago de Chile.Infórmese sobre la garantía estatal de los depósitos en su banco o
        en www\u200e.\u200dcmfchile\u200e.\u200dcl ©.Todos los derechos reservados.Hoja
        [http://contentz.mkt8988.com/lp/14944/107981/hoja.png] Comprometidos por un medio ambiente mejor, prefiera
        los medios digitales al papel impreso.
        [http://bancochile.cl/img/PS76JRn/pIolTcsauGpvWl9Atyie7MwN8CHjl3MRFXk=ttp://bancochile.cl/img/${id}]
        """.replace("\n", ""),
    }

    expense = Expense.get_expense(parsed_usd["content"])
    assert expense.value == 15.2
    assert expense.currency == Currency.USD
    assert expense.category == ExpenseCategory.ONLINE_PLATFORM, f"Invalid category for {expense.commerce}"
    assert expense.date == datetime(2025, 9, 12, 17, 24)

    expense = Expense.get_expense(parsed_clp["content"])
    assert expense.value == 7050.0
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.ONLINE_PLATFORM
    assert expense.date == datetime(2025, 9, 9, 17, 24)


def test_parse_data_giro():
    data = {
        "subject": "Giro con Tarjeta de Débito",
        "time": "2025-08-24T15:54:22.000Z",
        "content": """
            [http://contentz.mkt8988.com/lp/14944/107881/BCH_nuevo.png] Richard Hector Alexander Pe a
            Bonifaz:Te informamos que se ha realizado un giro en Cajero por $20.000 con cargo a
            Cuenta ****7204 el 24/08/2025 11:54.Revisa Saldos y Movimientos en App Mi Banco o Banco
            en Línea.Más información 60\u200d0 63\u200d7
            37\u200d37.[http://contentz.mkt8988.com/lp/14944/107981/aleta_BCH.png]Sigue estos
            consejos para evitar fraudes[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png]
            Nunca te llamaremos solicitando tus claves o información
            personal.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca hagas click
            en links ni descargues archivos adjuntos de correos
            sospechosos.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Ingresa a la
            página del Banco digitando la dirección en la barra de tu navegador.Realiza todo de
            forma ágil y simple usando nuestras
            aplicaciones*[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]Mi
            Banco[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\u200dMi
            Pass[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]Mi
            InversiónEncuéntranos[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
            bancochile\u200e.\u200dcl[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
            @\u200dAyudaBancoChile[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
            @\u200dBancodechile[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png] Banca
            Telefónica60\u200d0 63\u200d7 37\u200d37* Por seguridad, descarga las aplicaciones solo
            en las tiendas Google Play y App Store. Las Apps no están disponibles para teléfonos
            desbloqueados (Jailbreak o Rooteado).Este mensaje ha sido enviado a
            'richard.penab@gmail.com' con información exclusiva para clientes del banco. Banco de
            Chile. Casa Matriz: Ahumada 251, Santiago de Chile.Infórmese sobre la garantía estatal
            de los depósitos en su banco o en www\u200e.\u200dcmfchile\u200e.\u200dcl ©.Todos los
            derechos reservados.Hoja [http://contentz.mkt8988.com/lp/14944/107981/hoja.png]
            Comprometidos por un medio ambiente mejor, prefiera los medios digitales al papel
            impreso. [http://bancochile.cl/img/vQsmkQrjTnMVtFf7DhWzoXeYY2H89jTdPEgMlDpdcyg=ttp://bancochile.cl/img/${id}]"}
            """.replace("\n", ""),
    }

    expense = Expense.get_expense(data["content"])
    assert expense.value == 20000.0
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.GENERAL
    assert expense.date == datetime(2025, 8, 24, 11, 54)


def test_parse_transference():
    data = {
        "subject": "Transferencia a Terceros",
        "time": "2025-09-13T16:50:42.000Z",
        "content": """
            Logo Banco De Chile
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/logo_bch.png]
            Icono App Mi Banco
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/mi-banco/bch_app.pn
            g] Comprobante de Transferencia a terceros Estimado(a): Richard XXXXX Te
            informamos que has realizado una Transferencia a terceros en forma exitosa con el
            siguiente detalle: Origen Tipo de Cuenta Cuenta Corriente Nº de Cuenta XXXXXXXXX-04
            Destino Nombre y Apellido Francisco Moreira Herrera Rut XXXXXX076-X Tipo de Cuenta Cuenta
            Vista Nº de Cuenta XXXX421-98 Banco Banco Santander Email
            XXXXXXXX@ug.uchile.cl Monto $23.000 Mensaje Fecha y Hora:sábado 13 de
            septiembre de 2025
            13:50TransacciónTEFMBCO2509131350121174493190[https://servicios.bancochile.cl/imagenes/mo
            vil/correo/mails-assets/v2/mi-banco/bch_stamp.png] Si tienes dudas o consultas, puedes
            llamar a nuestra Banca Telefónica o también, dirigirte a cualquiera de nuestras
            sucursales. Icono facebook
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/icon_social_faceboo
            k.png]  bancochile.clTwitter
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/icon_social_twitter
            .png] @AyudaBancoChileIcono Instagram
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/icon_social_instagr
            am.png] @bancodechile600 637 37 37 Banca Telefónica Alerta
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/icon_alert.png] ES
            CLAVE NO DAR TUS CLAVES Por seguridad, este cuerpo no contiene enlaces al sítio Web de
            Banco de Chile Importante • Es clave no dar tu claves. • Nunca entregar claves,
            información financiera o datos personales a nadie. • Ingresar a la página del Banco
            digitando la dirección en la barra del navegador. • Nunca descargar archivos adjuntos
            de remitentes desconocidos. • Solo seguir nuestras cuentas oficiales certificadas en
            redes sociales (fijarse en el check junto al nombre de la cuenta). • Mantener
            actualizado el antivirus. • En caso de detectar actividad sospechosa, contactarnos a
            través de nuestros canales oficiales de ayuda. • Información de cómo evitar ser
            víctima de un fraude en nuestra página web. Banco de Chile. Casa Matriz: Ahumada 251,
            Santiago de Chile.Infórmese sobre la garantía estatal de los depósitos en su banco o
            en www.cmfchile.cl. © 2025.Todos los derechos reservados. Icono Hoja
            [https://servicios.bancochile.cl/imagenes/movil/correo/mails-assets/v2/icon_hoja.png]
            Comprometidos por un medio ambiente mejor, prefiera los medios digitales al papel impreso.
        """.replace("\n", ""),
    }

    transference = Transference.get_transference(data["content"], data["time"])
    assert transference.value == 23000.0
    assert transference.currency == Currency.CLP
    assert transference.recipient == "Francisco Moreira Herrera"
    assert transference.category == ExpenseCategory.GENERAL
    assert transference.date == datetime(2025, 9, 13, 16, 50, 42, tzinfo=timezone.utc).astimezone(TZ)


def test_parse_app_transference():
    data = {
        "subject": "Transferencias de Fondos a Medio de Pago Fintoc",
        "time": "2025-09-15T11:00:27.000Z",
        "content": """
        [http://login.bancochile.cl/bancochile-web/persona/login/assets/images/img-mails/logo-banc
        o-chile.png] ESTIMADO(A) RICHARD HECTOR ALEXANDER PEÑA BONIFAZLe informamos que usted ha
        efectuado una transferencia de fondos a Medio De Pago Fintoc, el día 15 de septiembre de
        2025, desde su Cuenta Corriente XXXX204. El detalle puede revisarlo a
        continuación[http://login.bancochile.cl/bancochile-web/persona/login/assets/images/img-ma
        ils/mipass.png] DESDE HOY PUEDES AUTORIZAR TUS TRANSFERENCIAS EN TU CELULAR CON LA
        APLICACION MI PASS EN VEZ DE DIGIPASS Y AHORRA TIEMPO.DESCARGA MI PASS DESDE GOOGLE PLAY
        O APPLE STORE. Datos del Destinatario Nombre Medio De Pago Fintoc Rut 77.XXX.XXX-5 Cuenta
        XXXXX017 Banco Banco Security Mail transferencias@fintoc.com Datos de la Transferencia
        Fecha 15/09/2025 Cuenta XXXX204 Monto $21.501 ID TEF_IPE2509150800121190279700 Mensaje
        1FIN-pi_32jVPObXpCDwHgCdfAWm4fK8mlC
        [http://login.bancochile.cl/bancochile-web/persona/login/assets/images/img-mails/timbre.pn
        g]
        [http://login.bancochile.cl/bancochile-web/persona/login/assets/images/img-mails/comproban
        te-cuida-clave.jpg]  * Por tu seguridad, este mensaje no tiene enlace al sitio web de
        Banco de Chile, además: * Nunca te pediremos ingresar a un sitio web desde un correo  *
        Nunca te pediremos ingresar tu clave Digipass antes del ingreso a tu Banco en Línea, ni
        al inicio de tu sesión * Nunca te llamaremos ni pediremos por SMS tus claves, datos
        personales o tu clave Digipass * Nunca hagas click en un link desde un correo porque
        puede llevarte a un sitio falso * Verifica siempre que la URL del Banco en Línea
        comience con https://(en vez de http://) * No hagas click en un link de resultado de
        búsqueda. Hasta un buscador puede no ser
        seguro.[http://login.bancochile.cl/bancochile-web/persona/login/assets/images/img-mails/lo
        go-bch-footer.png] Infórmese sobre la garantía estatal de los depósitos en su banco o
        en www.sbif.cl © 2019 Banco de Chile. Todos los Derechos Reservados.
        """.replace("\n", ""),
    }

    transference = Transference.get_transference(data["content"], data["time"])
    assert transference.value == 21501.0
    assert transference.currency == Currency.CLP
    assert transference.recipient == "Medio De Pago Fintoc"
    assert transference.category == ExpenseCategory.GENERAL
    assert transference.date == datetime(2025, 9, 15, 11, 00, 27, tzinfo=timezone.utc).astimezone(TZ)
