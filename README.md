# sshusercerts
Time based authentication for OpenSSH

sshusercerts is a Proof of Concept for duration based Authentication for OpenSSH. OpenSSH is widely 
used for system administration of Linux/Unix based systems. It can authenticate via username/password, 
via keys and via certificate. Authentication via certificates is the option we will use here.
Certificates are emitted by a centralized Certificate Authority and have an expiration date, very similar in
concept to SSL certificates for websites.These 2 characteristics make certificates an interesting choice for 
authentication as we gain centralized management and time based login capabilities. 

Prior Art:
- Google - BeyondCorp
- Netflix - Bless - https://github.com/Netflix/bless
- Facebook - blog post by Marlon https://code.fb.com/security/scalable-and-secure-access-with-ssh/
- Pritunl - https://zero.pritunl.com/
- scaleft - https://www.scaleft.com/product/server-access/ (now Okta)

OpenSSH is the default for Linux/Unix system administration, allowing the system administrator to have a text based terminal into a network connected, local or remote system. For authentication username/password is the default, but key based is a very
popular alternative. In key based authentication the user creates a private/public key pair and places the public 
key on the remote system and use their private key to authenticate - this  eliminates the need for username 
and password and provides a fast login experience. It is also the base for many automation options, as it can be used for a 
batch type login in user written scripts and other automation tools, for example Ansible. SSH is very powerful and many 
resources exist on the web exlaining its basic and advanced use: https://github.com/moul/awesome-ssh

In key based authentication the user creates a public/private key pair and copies the public key is copied to the target server. 
Then the private key is used to authenticate the user on the target server. The public key provides access as long as it exists, i.e. there is expiration attached to the keys. https://www.rosehosting.com/blog/ssh-login-without-password-using-ssh-keys/

In the certificate based approach we create a private and public key for a signing authority certificate (SAC).  
We then configure the targets to trust certificates that are signed by the private key of the SAC by copying 
the public key to each target. A user creates a public/private key as before, but needs to get their public key 
signed by the SAC. That signed public key is then used to authenticate to the target. Take a look at the following
article for a detailed description: https://linux-audit.com/granting-temporary-access-to-servers-using-signed-ssh-keys/

![Diagram 1](https://github.com/wkandek/sshusercerts/blob/master/sshusercerts_diag1.PNG)

Why introduce this complication?
- the targets now only need 1 public key to authenticate all users
  - imagine 100s/1000s of targets and 10s/100s of users 
- the certificate for the user can be time limited, say for 12 hours
  - this reduces the security exposure of key theft - in private/public key authentication key are eternal and if copied
    by an attacker can be used freely. Abuse has to be detected through other means, i.e. anomaly detection
  - a certificate, if copied will give the attacker access for only the validity of the certificate

The overhead caused is then only periodic, for example requiring daily renewal of the certificate  

OpenSSH natively supports certificates, but there is no mechanism for the emission of certificates or key signing.

The sshusercerts project includes a webservice that is performs the certificate emission. The sshusercerts service requires an 
authentication step plus the user's public key and returns a certificate, i.e. teh signed key. The sshusercerts project is 
implemented with 2 factor authentication (2FA) with username plus password and an OTP token, through Google Authenticator
or others.

Bonus:
Servers can also identify via a certificate to the users. If the user trusts the signing authority then the SSH question
on whether one is sure that a target is legitimate, can be avoided. The certificate for the server should be long lived to avoid
login problems. The server signing authority should be a separate public/private key as its usage is targeted a different
function.

Take a look at demo-setup.txt for a walk-through of the POC.

