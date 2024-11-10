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

InfiniBot runs inside a Docker container, so familiarity with Docker is a prerequisite for this project. You can find documentation for setting up Docker elsewhere.

Additionally, you need to have a Discord bot registered with Discord. There are many resources available online for registering a bot.

## Setup

Follow these steps to set up InfiniBot:

1. Clone the repository.
2. Run `./rebuild_and_run.bash` using a Bash terminal (other command line tools may work, but Bash is the supported one). Docker will begin building the container, which may take some time on the first run.
3. Once the build completes, InfiniBot will start, but you will see the following error message:
    ```
    FATAL ERROR: Token config file generated in ./generated/configure/TOKEN.json. Please configure your token!!!
    Exiting...
    ```
4. To resolve this, navigate to `./generated/configure/TOKEN.json` and add your Discord bot’s token to the `discord_auth_token` field.
    - **Note:** The `topgg_auth_token` field is for the token provided by Top.gg (a Discord bot listing website) to report InfiniBot's server count. Since this feature is only used on the official InfiniBot application, you should leave this as `None`.
5. Restart the bot by running `./rebuild_and_run.bash` again.
6. InfiniBot should now start up. Make sure to invite your bot to a server to get started.
7. You can configure additional settings in the `./generated/configure` folder, such as:
    - Default profane words to moderate.
    - Global status for all main features (can be overridden with admin commands).
    - Developer IDs, development server IDs, and other configuration settings (most settings should be left as is, as they are used for the official InfiniBot application).

## Console Commands

The following scripts are available to manage the project:

### `./build.bash`
Builds the project image without running it.

- **Arguments:**
  - `--use-cache` - Builds the project using cache, which speeds up the process.

### `./remove_container.bash`
Removes the project's container, but leaves the build image intact.

### `./run.bash`
Runs the project, assuming the image exists. The previous container must have been removed.

- **Arguments:**
  - `-d` - Runs the project in detached mode (no logs). You can stop the project by running `./remove_container.bash`.

### `./rebuild_and_run.bash`
Simplifies the process of rerunning the container after making changes. It stops the container, rebuilds it (using cache), and restarts it.

- **Arguments:**
  - `--no-cache` - Rebuilds the container without using cache, which will take longer but may resolve issues.

### `./run_then_exec.bash`
Runs the project in detached mode (like `./run.bash -d`) and then executes a shell inside the running container. This can be useful for running tests while the container is running.

## Credits

This project was created by [cypress.exe](https://github.com/cypress-exe). All rights reserved. Cloning and personal use of this project are allowed, but commercial or widespread use is prohibited.
