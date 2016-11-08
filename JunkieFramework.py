class Settings(object):
    def __init__(self,
                 email_sender="hypadmin@epmjunkie.com",
                 email_smtp_host="localhost",
                 email_smtp_port=25):
        self.email_sender = email_sender
        self.email_smtp_host = email_smtp_host
        self.email_smtp_port = email_smtp_port


class JunkieFramework(object):
    class _ContextGeneral:
        def __init__(self, context, value):
            self.context = context
            self.value = value

        def __str__(self):
            return self.context[self.value]

    class _ContextPeriod:
        class _Part:
            def __init__(self, key, item=0):
                self.key = key
                self.item = item

            def __str__(self):
                return str(self.key).split("-")[self.item].upper()

        def __init__(self, context):
            self.context = context
            self.Month = self._Part(self, 0)
            self.Year = self._Part(self, 1)

        def __str__(self):
            return self.context["PERIODNAME"]

    class _Email:
        def __init__(self, settings):
            self.sender = settings.email_sender
            self.host = settings.email_smtp_host
            self.port = settings.email_smtp_port

        # Handles sending email with optional attachments
        '''
        Sample usage:
        subject = "Data load has started"
        body = "Data load for location has started."
        recipients = can be a array ["hypadmin@epmjunkie.com","testing@epmjunkie.com"] or comma delimited list
        send(recipients=recipients, subject=subject, body=body)
        '''
        def send(self, recipients, body, subject="Test Message", attachment=[], sender=None,
                     host=None, port=None):
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            if not sender:
                sender = self.sender
            if not host:
                host = self.host
            if not port:
                port = self.port

            # Catch missing emails
            if len(recipients) == 0:
                recipients = sender
                recipients = [recipients]
                prefix = "Invalid Recipients - "
            else:
                # Check if its a comma delimited string already
                if "," in recipients:
                    recipients = [x.strip() for x in recipients.split(",")]
                else:
                    recipients = [recipients]

            client = smtplib.SMTP(host, port)
            message = MIMEMultipart()
            message["From"] = sender
            message["To"] = ', '.join(recipients)
            message["Subject"] = prefix + subject
            for item in attachment:
                message.attach(item)
            message.attach(MIMEText(body))
            client.sendmail(sender, recipients, message.as_string())
            client.quit()

        # Handles creating attachment for emailing
        def create_attachment(self, path, name):
            import mimetypes
            from email.mime.audio import MIMEAudio
            from email.mime.base import MIMEBase
            from email.mime.image import MIMEImage
            from email.mime.text import MIMEText
            from email import encoders
            try:
                self.api.logInfo("Create Attachment: " + name + " [" + path + "]")

                if len(name) > 0 and len(path) > 0:
                    contentType = mimetypes.guess_type(path)[0]

                    self.api.logInfo("Content Type: " + str(contentType))

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
            except:
                self.api.logInfo("Error occurred creating attachment.")
                return None

    def __init__(self, context, api, settings=Settings()):
        self.context = context
        self.api = api
        self.settings = settings
        self.LoadID = self._ContextGeneral(context=context, value="LOADID")
        self.Rule = self._ContextGeneral(context=context, value="RULENAME")
        self.RuleID = self._ContextGeneral(context=context, value="RULEID")
        self.Location = self._ContextGeneral(context=context, value="LOCNAME")
        self.Period = self._ContextPeriod(context=context)
        self.PeriodKey = self._ContextGeneral(context=context, value="PERIODKEY")
        self.Category = self._ContextGeneral(context=context, value="CATNAME")
        self.CategoryKey = self._ContextGeneral(context=context, value="CATKEY")
        self.TargetApp = self._ContextGeneral(context=context, value="TARGETAPPNAME")
        self.TargetAppID = self._ContextGeneral(context=context, value="APPID")
        self.ImportFormat = self._ContextGeneral(context=context, value="IMPORTFORMAT")
        self.Email = self._Email(settings=settings)