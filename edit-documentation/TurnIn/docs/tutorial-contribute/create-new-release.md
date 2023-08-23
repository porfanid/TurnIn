---
sidebar_position: 3
---

# Create a new release

The process of creating the release files happens within github workflows so that I can be sure that multiple operating systems are supported. For now, I have created releases that create an exe app, a deb file and a mac os dmg app.

## Benefits of using github workflows

By using github workflows, we can be sure

1. that the files created will work(becase the release file will create the package in the exact same way every time)

1. That we will not have to reread the process every time, thus saving a lot of time when creating packages

1. That the user who makes a change has already created packages for his release.

1. Packages for many operating systems are generated even though the user is using only one of them.

## How to create a release workflow

If you want to create another release file you should create a workflow that creates the package. You are requested to test the package and send me screenshots and preferably log files of the package that you created. After I conclude that the package is working correctly, I will merge the pull request.

The screenshots should be like the ones that I uploaded for every phase of the program. Otherwise, it may have a bug creating a connection(most common problem).