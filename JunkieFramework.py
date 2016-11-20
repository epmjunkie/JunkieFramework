class Settings(object):
    def __init__(self,
                 email_sender="hypadmin@epmjunkie.com",
                 email_smtp_host="localhost",
                 email_smtp_port=25,
                 email_smtp_password=None,
                 email_smtp_tls=False):
        self.email_sender = email_sender
        self.email_smtp_password = email_smtp_password
        self.email_smtp_host = email_smtp_host
        self.email_smtp_tls = email_smtp_tls
        self.email_smtp_port = email_smtp_port


class Core(object):
    class _Log:
        def __init__(self, context, api, seperator=":\t", delimiter="\n"):
            self._context = context
            self.api = api
            self.seperator = seperator
            self.delim = delimiter

        def _parse(self, obj, seperator=None, delimiter=None):
            if not delimiter:
                delimiter = self.delim
            if not seperator:
                seperator = self.seperator
            return delimiter.join(["%s%s%s" % (key, seperator, value) for (key, value) in sorted(obj.items())])

        def object(self, obj, prefix="Object: ", seperator=None, delimiter=None):
            if obj:
                return "%(prefix)s%(list)s" % {"prefix": prefix, "list": self._parse(obj, seperator, delimiter)}
            return "%sEmpty" % prefix

        def context(self):
            if self.context:
                self.api.logDebug(self.object(self._context, prefix="FDM Context:\n"))
            else:
                self.api.logWarn(self.object(self._context, prefix="FDM Context: "))

    class _Email:
        def __init__(self, settings):
            self.sender = settings.email_sender
            self.host = settings.email_smtp_host
            self.port = settings.email_smtp_port
            self.password = settings.email_smtp_password
            self.tls = settings.email_smtp_tls

        # Handles sending email with optional attachments
        '''
        Sample usage:
        subject = "Data load has started"
        body = "Data load for location has started."
        recipients = can be a array ["hypadmin@epmjunkie.com","testing@epmjunkie.com"] or comma delimited list
        send(recipients=recipients, subject=subject, body=body)
        '''
        def send(self, recipients, body, subject="Test Message", attachment=[], sender=None,
                     host=None, port=None, password=None, tls=None):
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            if not sender:
                sender = self.sender
            if not host:
                host = self.host
            if not port:
                port = self.port
            if not password:
                password = self.password
            if tls is None:
                tls = self.tls


            # Catch missing emails
            if len(recipients) == 0:
                recipients = sender
                recipients = [recipients]
                subject = "Invalid Recipients - " + subject
            else:
                # Check if its a comma delimited string already
                if "," in recipients:
                    recipients = [x.strip() for x in recipients.split(",")]
                else:
                    recipients = [recipients]

            client = smtplib.SMTP(host, port)
            if tls:
                client.ehlo()
                client.starttls()
                client.ehlo()
            if password:
                client.login(sender, password)
            message = MIMEMultipart()
            message["From"] = sender
            message["To"] = ', '.join(recipients)
            message["Subject"] = subject
            for item in attachment:
                message.attach(item)
            message.attach(MIMEText(body))
            client.sendmail(sender, recipients, message.as_string())
            client.quit()
            client.close()

        # Handles creating attachment for emailing
        def create_attachment(self, path, name):
            import mimetypes
            from email.mime.audio import MIMEAudio
            from email.mime.base import MIMEBase
            from email.mime.image import MIMEImage
            from email.mime.text import MIMEText
            from email import encoders
            if len(name) > 0 and len(path) > 0:
                contentType = mimetypes.guess_type(path)[0]

                if contentType is None:
                    contentType = "text/plain"

                maintype, subtype = contentType.split("/", 1)

                f = open(path)
                if maintype == "text":
                    attachment = MIMEText(f.read(), _subtype=subtype)
                elif maintype == "image":
                    attachment = MIMEImage(f.read(), _subtype=subtype)
                elif maintype == "audio":
                    attachment = MIMEAudio(f.read(), _subtype=subtype)
                else:
                    attachment = MIMEBase(_maintype=maintype, _subtype=subtype)
                    attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                f.close()
                attachment.add_header("Content-Disposition", "attachment", filename=name)

                return attachment
            return None

    def __init__(self, context, api, settings=Settings()):
        self._context = context
        self._api = api
        self.settings = settings
        self.Email = self._Email(settings=settings)
        self.log = self._Log(context, api)

    def getContextValue(self, name):
        return str(self._context[name])

    @property
    def ApplicationID(self):
        return self.getContextValue("APPID")

    @property
    def BatchScriptDirectory(self):
        return self.getContextValue("BATCHSCRIPTDIR")

    @property
    def Category(self):
        return self.getContextValue("CATNAME")

    @property
    def CategoryKey(self):
        return self.getContextValue("CATKEY")

    @property
    def CheckStatus(self):
        return self.getContextValue("CHKSTATUS")

    @property
    def EpmHome(self):
        return self.getContextValue("EPMORACLEHOME")

    @property
    def EpmInstanceHome(self):
        return self.getContextValue("EPMORACLEINSTANCEHOME")

    @property
    def ExportFlag(self):
        return self.getContextValue("EXPORTFLAG")

    @property
    def ExportMode(self):
        return self.getContextValue("EXPORTMODE")

    @property
    def ExportStatus(self):
        return self.getContextValue("EXPSTATUS")

    @property
    def FileDirectory(self):
        return self.getContextValue("FILEDIR")

    @property
    def FileName(self):
        return self.getContextValue("FILENAME")

    @property
    def ImportFlag(self):
        return self.getContextValue("IMPORTFLAG")

    @property
    def ImportFormat(self):
        return self.getContextValue("IMPORTFORMAT")

    @property
    def ImportStatus(self):
        return self.getContextValue("IMPSTATUS")

    @property
    def InboxDirectory(self):
        return self.getContextValue("INBOXDIR")

    @property
    def LoadID(self):
        return self.getContextValue("LOADID")

    @property
    def LocationKey(self):
        return self.getContextValue("LOCKEY")

    @property
    def Location(self):
        return self.getContextValue("LOCNAME")

    @property
    def MultiPeriodLoad(self):
        return self.getContextValue("MULTIPERIODLOAD")

    @property
    def OutboxDirectory(self):
        return self.getContextValue("OUTBOXDIR")

    @property
    def Period(self):
        return self.getContextValue("PERIODNAME")

    @property
    def PeriodKey(self):
        return self.getContextValue("PERIODKEY")

    @property
    def ProcessStatus(self):
        return self.getContextValue("PROCESSSTATUS")

    @property
    def Rule(self):
        return self.getContextValue("RULENAME")

    @property
    def RuleID(self):
        return self.getContextValue("RULEID")

    @property
    def ScriptDirectory(self):
        return self.getContextValue("SCRIPTSDIR")

    @property
    def SourceName(self):
        return self.getContextValue("SOURCENAME")

    @property
    def SourceType(self):
        return self.getContextValue("SOURCETYPE")

    @property
    def TargetApp(self):
        return self.getContextValue("TARGETAPPNAME")

    @property
    def TargetAppDB(self):
        return self.getContextValue("TARGETAPPDB")

    @property
    def TargetAppID(self):
        return self.getContextValue("APPID")

    @property
    def ValidationStatus(self):
        return self.getContextValue("VALSTATUS")