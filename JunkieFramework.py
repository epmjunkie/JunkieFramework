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
    class _ContextGeneral:
        def __init__(self, context, value):
            self.context = context
            self.value = value

        def __str__(self):
            return self.context[self.value]

    class _ContextPeriod:
        class _Part:
            def __init__(self, key, item=0):
                self.key = str(key)
                self.item = item
                self.items = [None, None]
                if self.key:
                    import re
                    self.items[0] = re.search('\D+', self.key).group(0)
                    self.items[1] = re.search('\d+', self.key).group(0)

            def __str__(self):
                import re
                items = []
                return self.items[self.item].upper()

        def __init__(self, context):
            self.context = context
            self.Month = self._Part(self, 0)
            self.Year = self._Part(self, 1)

        def __str__(self):
            if "PERIODNAME" in self.context:
                return self.context["PERIODNAME"]
            return ""

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
                client.ehlo
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
        self.context = context
        self.api = api
        self.settings = settings
        self.ApplicationID = self._ContextGeneral(context=context, value="APPID")
        self.BatchScriptDirectory = self._ContextGeneral(context, value="BATCHSCRIPTDIR")
        self.Category = self._ContextGeneral(context=context, value="CATNAME")
        self.CategoryKey = self._ContextGeneral(context=context, value="CATKEY")
        self.CheckStatus = self._ContextGeneral(context=context, value="CHKSTATUS")
        self.EpmHome = self._ContextGeneral(context=context, value="EPMORACLEHOME")
        self.EpmInstanceHome = self._ContextGeneral(context=context, value="EPMORACLEINSTANCEHOME")
        self.ExportFlag = self._ContextGeneral(context=context, value="EXPORTFLAG")
        self.ExportMode = self._ContextGeneral(context=context, value="EXPORTMODE")
        self.ExportStatus = self._ContextGeneral(context=context, value="EXPSTATUS")
        self.FileDirectory = self._ContextGeneral(context=context, value="FILEDIR")
        self.FileName = self._ContextGeneral(context=context, value="FILENAME")
        self.ImportFlag = self._ContextGeneral(context=context, value="IMPORTFLAG")
        self.ImportFormat = self._ContextGeneral(context=context, value="IMPORTFORMAT")
        # todo find out what IMPST is in the context.
        self.ImportStatus = self._ContextGeneral(context=context, value="IMPSTATUS")
        self.InboxDirectory = self._ContextGeneral(context=context, value="INBOXDIR")
        self.LoadID = self._ContextGeneral(context=context, value="LOADID")
        self.LocationKey = self._ContextGeneral(context=context, value="LOCKEY")
        self.Location = self._ContextGeneral(context=context, value="LOCNAME")
        self.MultiPeriodLoad = self._ContextGeneral(context=context, value="MULTIPERIODLOAD")
        self.OutboxDirectory = self._ContextGeneral(context=context, value="OUTBOXDIR")
        self.Period = self._ContextPeriod(context=context)
        self.PeriodKey = self._ContextGeneral(context=context, value="PERIODKEY")
        self.ProcessStatus = self._ContextGeneral(context=context, value="PROCESSSTATUS")
        self.Rule = self._ContextGeneral(context=context, value="RULENAME")
        self.RuleID = self._ContextGeneral(context=context, value="RULEID")
        self.ScriptDirectory = self._ContextGeneral(context=context, value="SCRIPTSDIR")
        self.SourceName = self._ContextGeneral(context=context, value="SOURCENAME")
        self.SourceType = self._ContextGeneral(context=context, value="SOURCETYPE")
        self.TargetApp = self._ContextGeneral(context=context, value="TARGETAPPNAME")
        self.TargetAppDB = self._ContextGeneral(context=context, value="TARGETAPPDB")
        self.TargetAppID = self._ContextGeneral(context=context, value="APPID")
        self.ValidationStatus = self._ContextGeneral(context=context, value="VALSTATUS")
        self.Email = self._Email(settings=settings)

