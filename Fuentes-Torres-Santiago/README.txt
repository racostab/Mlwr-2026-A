Fuentes Torres Santiago ----------------------------------------

Mlwr-2026-A/
└── Fuentes-Torres-Santiago/
    │
    ├── Entrega1/                      ← Partes 1, 2 y 3
    │   ├── scriptVM.bat                Control VirtualBox CLI
    │   ├── vm.py                       Control VirtualBox API
    │   ├── control_qemu.bat            (FALTA) Control QEMU CLI
    │   ├── programa_qemu.py            (FALTA) Control QEMU API
    │   ├── ssh_login.bat               SSH login CLI
    │   ├── ssh_cmd.bat                 SSH cmd CLI
    │   ├── ssh.py                      SSH API
    │   ├── docker_login.bat            Docker login CLI
    │   ├── docker_cmd.bat              Docker cmd CLI
    │   └── docker.py                   Docker API
    │
    └── Entrega2/                      ← Parte 4 (Laboratorio)
        │
        ├── alma_srv.py                ← Servidor
        ├── alma_clt.py                ← Cliente CLI
        ├── alma_gui.py                ← Cliente GUI
        │
        ├── modulos/                   ← Análisis estático
        │   ├── hashes.py          
        │   ├── entropia.py        
        │   ├── tipo_archivo.py    
        │   ├── cadenas.py        
        │   └── ssdeep.py                  │
        ├── infraestructura/           ← Reusar de Entrega1
        │   ├── vm.py              (copia/referencia)
        │   ├── ssh.py             (copia/referencia)
        │   └── docker.py          (copia/referencia)
        │
        ├── experimentos/              ← Archivos de prueba
        │   └── (muestras de malware)
        │
        ├── config.py                  ← Configuración global
        └── README.md                  ← Instrucciones