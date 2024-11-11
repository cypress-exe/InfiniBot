# InfiniBot

InfiniBot is a multipurpose Discord utility bot designed to scale across thousands of servers using SQLite for storage and sharding for distribution. InfiniBot offers a variety of features including:
- Profanity moderation
- Spam moderation
- Message and action logging
- Leveling with rewards
- Join/leave messages
- Reaction roles
- Role messages
- Birthday messages
- And more!

Although this project is not open for external contributions at the moment, you are welcome to clone and host it on your own server.

## Prerequisites

InfiniBot runs inside a Docker container, so Docker must already be installed. You can find documentation for setting up Docker elsewhere.

Additionally, you need to have a Discord bot registered with Discord. There are many resources available online for registering a bot.

## Setup

Follow these steps to set up InfiniBot for a linux environment. Some steps may vary for certain operating systems.

1. Clone the repository with `git clone https://github.com/cypress-exe/InfiniBot.git`.
2. Run `sudo bash build.bash` using a Bash terminal (other command line tools may work, but Bash is the supported one). Docker will begin building the container, which may take some time on the first run.
3. Run `sudo bash run.bash` to run the container.
4. Once the build completes, InfiniBot will start, but you will see the following error message:
    ```
    FATAL ERROR: Token config file generated in ./generated/configure/TOKEN.json. Please configure your token!!!
    Exiting...
    ```
5. To resolve this, navigate to `./generated/configure/TOKEN.json` and add your Discord bot’s token to the `discord_auth_token` field.
    - **Note:** The `topgg_auth_token` field is for the token provided by Top.gg (a Discord bot listing website) to report InfiniBot's server count. Since this feature is only used on the official InfiniBot application, you should leave this as `None`.
6. Restart the bot by running `sudo bash rebuild_and_run.bash` again.
7. InfiniBot should now start up. Make sure to invite your bot to a server to get started.
8. You can configure additional settings in the `./generated/configure` folder, such as:
    - Default profane words to moderate.
    - Global status for all main features (can be overridden with admin commands).
    - Developer IDs, development server IDs, and other configuration settings (most settings should be left as is, as they are used for the official InfiniBot application).

## Console Commands

The following scripts are available to manage the project:

### `sudo bash build.bash`
Builds the project image without running it.

- **Arguments:**
  - `--use-cache` - Builds the project using cache, which speeds up the process.

### `sudo bash remove_container.bash`
Removes the project's container, but leaves the build image intact.

### `sudo bash run.bash`
Runs the project, assuming the image exists. The previous container must have been removed.

- **Arguments:**
  - `-d` - Runs the project in detached mode (no logs). You can stop the project by running `sudo bash remove_container.bash`.

### `sudo bash rebuild_and_run.bash`
Simplifies the process of rerunning the container after making changes. It stops the container, rebuilds it (using cache), and restarts it.

- **Arguments:**
  - `--no-cache` - Rebuilds the container without using cache, which will take longer but may resolve issues.

### `sudo bash run_then_exec.bash`
Runs the project in detached mode (like `sudo bash run.bash -d`) and then executes a shell inside the running container. This can be useful for running tests while the container is running.

## Credits

This project was created by [cypress.exe](https://github.com/cypress-exe). All rights reserved. Cloning and personal use of this project are allowed, but commercial or widespread use is prohibited.
