## Para iniciar la Vm necesitamos usar PowerShell en modo administrador
## Una vez con los privilegios de administrador 
Iniciaremos nuestro SSH agent, con estos comandos
```
Set-Service ssh-agent -StartupType Automatic
Start-Service ssh-agent
```

## Se solocitara la contraseña de la llave publica, si se ejecuta por primera vez.