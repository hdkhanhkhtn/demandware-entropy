**Please consider using https://bitbucket.org/demandware/entropy, we have joined forces to work on a single Demandware plugin for SublimeText.**

# Demandware Server Upload for Sublime Text 3

This is an extension for Sublime Text 3 which will upload the current file to the configured Demandware server.

# Installation

Open *Package Control* in Sublime Text and select the Demandware plugin

OR

you can clone this repository into ```Sublime Text 3/Packages/Demandware```

Now you need to restart Sublime Text and then you should see a new menu item *Demandware Server Upload* in the *Tools* menu. There you can open the preferences and add your hostname, username and password for the upload.

```
{
	"instance": "instance-realm-customer.demandware.net",
	"username": "admin",
	"password": "***",
	"version": "version1",
	"enabled": "true"
}
```

That's it, go to a file in a cartridge, hit *Save* and it will get uploaded.

If you want to upload an entire cartridge, you can do so by selecting this option from the menu.

# Release history

- 2015/03/26 - [0.2.2](https://bitbucket.org/demandware/demandware-sublime-plugin/commits/tag/0.2.2)
    - Fixed issue #9: Authozization error now shows error dialog and exits the thread
- 2015/03/26 - [0.2.0](https://bitbucket.org/demandware/demandware-sublime-plugin/commits/tag/0.2.0)
    - Fixed issue #4: Upload now uses threads not blocking the UI anymore
- 2015/03/23 - [0.1.2](https://bitbucket.org/demandware/demandware-sublime-plugin/commits/tag/0.1.2)
    - Added 'Upload all cartridges' functionality
- 2015/03/05 - [0.1.1](https://bitbucket.org/demandware/demandware-sublime-plugin/commits/tag/0.1.1)
    - fixes to make upload work on Windows
- 2015/02/17 - [0.1.0](https://bitbucket.org/demandware/demandware-sublime-plugin/commits/tag/0.1.0)
    - added cartridge upload
    - minor improvements
    - refactored code
- 2015/02/13 - [0.0.1](https://bitbucket.org/demandware/demandware-sublime-plugin/commits/tag/0.0.1)
    - initial version with upload on save

# Support / Contributing

Please feel free to create issues and enhancement requests or discuss on the existing ones, this will help us understanding in which area the biggest need is. For discussions please start a topic on the [Community Suite discussion board](https://xchange.demandware.com/community/developer/community-suite/content).

# License

This plugin is provided under MIT license.