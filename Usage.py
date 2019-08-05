def append_path(value):  # don't append if its already there
    import sys
    if value not in sys.path:
        sys.path.append(value)

append_path('%(script_path)s\custom' % {'script_path': fdmContext["SCRIPTSDIR"]})
import JunkieFramework
reload(JunkieFramework)

#Usage Example
settings = JunkieFramework.Settings(email_sender='fdmee@epmjunkie.com', email_smtp_host="smtp.epmjunkie.com")
jf = JunkieFramework.Core(context=fdmContext, api=fdmAPI, settings=settings)


def test():
    fdmAPI.logDebug(jf.ImportFormat)
    fdmAPI.logDebug(jf.Period)
    attachments = []
    attachments.append(jf.Email.create_attachment(path=r"c:\temp\test1.zip", name="test1.zip"))
    attachments.append(jf.Email.create_attachment(path=r"c:\temp\test2.zip", name="test2.zip"))
    jf.Email.send(recipients="test@epmjunkie.com", subject="testing", attachment=attachments, body="Test Email")