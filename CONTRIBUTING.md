# Contributing

When fixing bugs or contributing new features to the `aiida-cusp` plugin, please first discuss the change you wish to make via a new issue with the owners of this repository before making a change.
You may open a new issue at any time [here](https://github.com/astamminger/aiida-cusp/issues).
Once an issue is opened you may contribute your changes to the plugin by opening a pull request following the step-by-step guide described in the following.

## Creating a Pull Request

1. [Create a fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) of the `aiida-cusp` repository.
2. Setup a new branch in the created fork to add your changes, i.e.

	 ```
	 git checkout -b issue_123_your_branch_name
	 ```

3. Add your changes and commit them to the local branch you created in the previous step.
	 Ensure to always add proper tests and to update the documentation when fixing bugs or adding new features to the plugin.
	 Note that for contributing workflows it is required that you add at least one example using your workflow to the tutorials section in the documentation.
4. Once you're finished with your changes push them to your forked repository

	 ```
   git push origin issue_123_your_branch_name
	 ```

5. Finally go to your fork and create a new [pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request) on GitHub to the development branch, i.e. `aiida-cusp/develop`.
	 Please use a short, one sentence description for the pull request's title stating why this request has been created and provide a more concise description of the changes, including the issue number that is addressed by the changes, in the pull request's description.
6. After opening the pull request the automatic tests will start. Wait for the tests to finish and fix all failing tests (Pushing new changes to the open pull request will retrigger the tests)
7. Once all tests pass successfully your pull request is ready for review.
