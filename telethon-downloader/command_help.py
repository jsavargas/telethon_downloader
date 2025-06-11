import textwrap

class CommandHelp:
    help_text = textwrap.dedent('''
        Welcome to the bot!

        Available commands:
        /pyrogram - Displays the Telethon version
        /ytdlp - Displays the ytdlp version
        /version - Displays the bot version
        /id - Displays the user/group ID.
            - Usage: Simply type /id and the bot will respond with the ID of the current chat, whether it is a user or a group.

        /rename <new_name> - Rename the replied message file.
            - Usage: Reply to a message containing a file with /rename followed by the new name you want for the file.
            - Example: If you receive a document and want to rename it to "MyDocument", reply to the message with /rename MyDocument.
                - /rename 
                - /rename /NewDirectory
                - /rename newFileName
                - /rename NewFileName.ext
                - /rename Directory/NewFileName.ext
            - Note: The new name must not contain special characters that are not allowed in file names. You can also use /rename alone and it will rename according to the config.ini file rules

        /move <new_folder> - Moves the file from the replied message.
            - Usage: Reply to a message containing a file with /move followed by the new folder name you want. If no path is provided, it will move the file to the folder specified for the file or group in the config.ini file.
            - Example: If you receive a document and want to move it to "MyDocument", reply to the message with /move MyDocument.
                - /move
                - /move /NewDirectory

        /addextensionpath <extension> <NewDirectory> - Creates a download path rule based on file extension
            - Usage: Reply to a message containing a file with /addextensionpath followed by the new folder name you want. If no path is provided, it will create the rule using the extension as the folder name.
            - Example: If you receive a document and want to create a rule to direct those files to a folder named "MyFolder", reply to the message with /addextensionpath MyFolder. Then, you can use /move to move the file to the new path created with /addextensionpath.
                - /addextensionpath
                - /addextensionpath <REPLY>
                - /addextensionpath <REPLY> /NewDirectory
                - /addextensionpath <extension> /NewDirectory

        /delextensionpath <extension> - Deletes the download folder rule for the specified extension
            - Usage: Reply to a message containing a file with /delextensionpath to delete the extension rule.
            - Example: If you want to delete a rule, reply to the message with /delextensionpath.
                - /delextensionpath <extension>
                - /delextensionpath <REPLY>

        /addgrouppath
        /delgrouppath

    ''')

    ehelp_text = textwrap.dedent('''
        Welcome to the bot!

        Available commands:

        

        /addextensionpath <extension> <NewDirectory> - Crea una regla de ruta de descargad e archivo segun extension
            - Uso: Responde a un mensaje que contenga un archivo con /addextensionpath seguido del nuevo nombre que deseas para la carpeta. Si no agregas una ruta
            - Ejemplo: Si recibes un documento y quieres crear una regla para que esos archivos vayan a una carpeta "MiCarpeta", responde al mensaje con /addextensionpath MiCarpeta, luego puedes escribir /move para mover el archivo a la nueva ruta creada con /addextensionpath
                - /addextensionpath 
                - /addextensionpath <REPLY> /NuevoDirectorio
                - /addextensionpath <extension> /NuevoDirectorio


        /rename <new_name> - Rename the replied message file.
            - Usage: Reply to a message containing a file with /rename followed by the new name you want for the file.
            - Example: If you receive a document and want to rename it to "MyDocument", reply to the message with /rename MyDocument.
                - /rename 
                - /rename /NewDirectory
                - /rename newFileName
                - /rename NewFileName.ext
                - /rename Directory/NewFileName.ext
            - Note: The new name must not contain special characters that are not allowed in file names. You can also use /rename alone and it will rename according to the config.ini file rules


        /move <new_folder> - Mueve el archivo del mensaje respondido.
            - Uso: Responde a un mensaje que contenga un archivo con /move seguido del nuevo nombre que deseas para la carpeta. Si no agregas una ruta, se movera a la carpeta segun las para el archivo o grupo en el archivo config.ini
            - Ejemplo: Si recibes un documento y quieres moverlo a "MiDocumento", responde al mensaje con /move MiDocumento.
                - /move 
                - /move /NuevoDirectorio

        /addgroup <group_id> <new_folder> - Crea una nueva regla para descargar los archivos de este grupo en una carpeta especifica.
            - Uso: Responde a un mensaje que contenga un archivo con /addgroup seguido del nuevo nombre que deseas para la carpeta.
            - Ejemplo: Si recibes un documento y quieres crear una regla para que esos archivos vayan a una carpeta "MiCarpeta", responde al mensaje con /addgroup MiCarpeta, luego puedes escribir /move para mover el archivo a la nueva ruta creada con /addgroup
                - /addgroup 
                - /addgroup <REPLY> /NuevoDirectorio
                - /addgroup <group_id> /NuevoDirectorio

        /delgroup DEVELOP <new_folder> - Crea una nueva regla para descargar los archivos de este grupo en una carpeta especifica.
            - Uso: Responde a un mensaje que contenga un archivo con /addgroup seguido del nuevo nombre que deseas para la carpeta.
            - Ejemplo: Si recibes un documento y quieres crear una regla para que esos archivos vayan a una carpeta "MiCarpeta", responde al mensaje con /addgroup MiCarpeta, luego puedes escribir /move para mover el archivo a la nueva ruta creada con /addgroup
                - /addgroup 
                - /addgroup /NuevoDirectorio


        /addrenamegroup <group_id> - Crea una regla para renombrar archivos en base al texto del mensaje en el archivo a descargar.
            - Uso: Responde a un mensaje que contenga un archivo con /addrenamegroup para que sea agregada una nueva regla en el archivo config.ini.
            - Ejemplo: Si recibes un documento y quieres que su nombre sea el contenido del mensaje, responde al mensaje con /addrenamegroup. Puede usarse despues /rename para renomrar el archivo descargado segun las regla anteriormente creada.
                /addrenamegroup
                /addrenamegroup <group Id>

        /delrenamegroup <group_id> - Crea una regla para renombrar archivos en base al texto del mensaje en el archivo a descargar.
            - Uso: Responde a un mensaje que contenga un archivo con /delrenamegroup para que sea agregada una nueva regla en el archivo config.ini.
            - Ejemplo: Si recibes un documento y quieres que su nombre sea el contenido del mensaje, responde al mensaje con /delrenamegroup. Puede usarse despues /rename para renomrar el archivo descargado segun las regla anteriormente creada.
                /delrenamegroup
                /delrenamegroup <group Id>

        Pronto se agregarán más comandos. ¡Mantente atento!

        Los comandos pueden usarse tanto en chats privados como en chats grupales.
        Asegúrate de que el bot tenga los permisos necesarios para acceder a mensajes y archivos en los chats grupales.
    
    
    
    ''')

    @classmethod
    def get_help(cls):
        return cls.help_text

    @classmethod
    def get_ehelp(cls):
        return cls.ehelp_text
