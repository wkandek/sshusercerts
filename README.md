# sshusercerts
Time based authentication for OpenSSH

sshusercerts is a Proof of Concept for duration based Authentication for OpenSSH. OpenSSH can 
authenticate via certificates which are emitted by Certifcate Authority and have an expiration date.
These 2 characteristics make certificates an intersting choice for authentication as you gain 
centralized management and time based login capabilities. 

Prior Art:
- Google - BeyondCorp
- Netflix -
- Facebook - blog post by Marlon
- Dropbox 

SSH is widely used for system administration of Linux/Unix based systems.
It can authenticate via username/password, via keys and via certificate.
Username/password is the default, key based is very popular as it eliminates the need for username and password
and provides a fast login experience. It is also the base for many automation options, as it can be used in user written scripts
and other automation tools, for example Ansible.

In key based authentication the user creates a public/private key pair and the public key is copied to the target server. 
Then the private key can be used to authenticate the user on the target server. The public key has to be copied to all 
target servers and provides access as long as it exists, i.e. there is expiration attached to the keys

In the certificate based approach we create a private and public key for a signing authority certificate (SAC) . We then configure the targets
to trust certificates that are signed by the private key of the SAC by copying the public key to each target.
A user creates a public/private key as before, but needs to get their public key signed by the SAC. That signed public key is then
used to authenticate to the target.

Why introduce this complication?
- the targets now only need 1 public key to authenticate all users
  - imagine 100s/1000s of targets and 10s/100s of users 
- the certificate for the user can be time limited, for example for 12 hours
  - this reduces the security exposure of key theft - in private/public key authentication key are eternal and if copied
    by an attacker can be used freely. Abuse has to be detected through other means, i.e. anomaly detection
  - a certificate, if copied will give the attacker access for only the validity of the certificate

The overhead caused is then only periodic, for example daily renewal of the certificate  

OpenSSH natively supports certificates, but there is no mechanism for the emission of certificates process.

The sshusercerts project includes a webservice that is performs the certificate emission. The sshusercerts service requires an 
authentication step plus the user's public key and returns a signed certificate. The sshusercerts project is implemented with 2 factor authentication (2FA)
with username plus password and an OTP token, for example through Google Authenticator.

Bonus:
Servers can also identify via a certificate to the users. If the user trusts the signing authority then the SSH question
on whether one is sure that a target is legitimate, can be avoided. The certificate for the server should be long lived to avoid
login problems. The server signing authority should be a separate public/private key as its usage is targeted a different
function.
