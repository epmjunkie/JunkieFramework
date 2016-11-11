import sys
sys.path.append('%(script_path)s\custom' % {'script_path': fdmContext["SCRIPTSDIR"]})

import JunkieFramework as jframe
reload(jframe)

#Usage Example
settings = jframe.Settings(email_sender='fdmee@epmjunkie.com', email_smtp_host="smtp.epmjunkie.com")
jf = jframe.Core(context=fdmContext, api=fdmAPI, settings=settings)


def test():
    fdmAPI.logDebug(jf.ImportFormat)
    fdmAPI.logDebug(jf.Period)
    fdmAPI.logDebug(jf.Period.Month)
    fdmAPI.logDebug(jf.Period.Year)
    attachments = []
    attachments.append(jf.Email.create_attachment(path=r"c:\temp\test1.zip", name="test1.zip"))
    attachments.append(jf.Email.create_attachment(path=r"c:\temp\test2.zip", name="test2.zip"))
    jf.Email.send(recipients="test@epmjunkie.com", subject="testing", attachment=attachments, body="Test Email")