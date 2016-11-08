from JunkieFramework import Settings as jSet
from JunkieFramework import JunkieFramework as jFrame

#Usage Example
settings = jSet(email_smtp_host="smtp.epmjunkie.com")

def test():
    t = jFrame(context=context, api=fdmAPI, settings=settings)
    print(t.ImportFormat)
    print(t.Period)
    print(t.Period.Month)
    print(t.Period.Year)
    attachments = []
    attachments.append(t.Email.create_attachment(path=r"c:\temp\test1.zip"))
    attachments.append(t.Email.create_attachment(path=r"c:\temp\test2.zip"))
    t.Email.send(recipients="test@epmjunkie.com", subject="testing", attachments=attachments, body="Test Email")