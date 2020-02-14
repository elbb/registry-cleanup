package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/AlecAivazis/survey/v2"
	registry "github.com/nokia/docker-registry-client/registry"
)

var (
	imagesIndex []string
	tagsIndex   []string
	address     *string
	user        *string
	dryRun      *bool
)

type exitMenuType string

const (
	exitMenu exitMenuType = "Exit"
)

func getImages(hub *registry.Registry) ([]string, error) {
	repositories, err := hub.Repositories()
	if err != nil {
		return nil, err
	}
	return repositories, nil
}

func getTags(hub *registry.Registry, image string) ([]string, error) {
	tags, err := hub.Tags(image)
	if err != nil {
		return nil, err
	}
	return tags, err
}

func deleteTags(hub *registry.Registry, image string, tags []string) error {
	for _, v := range tags {
		err := deleteTag(hub, image, v)
		if err != nil {
			return err
		}
	}
	return nil
}

func deleteTag(hub *registry.Registry, image, tag string) error {
	digest, err := hub.ManifestV2Digest(image, tag)
	if err != nil {
		return err
	}
	if *dryRun == true {
		log.Printf("[DRYRUN] Deleting tag '%s' for image '%s'\n", tag, image)
	} else {
		log.Printf("Deleting tag '%s' for image '%s'\n", tag, image)
		err := hub.DeleteManifest(image, digest)
		if err != nil {
			return err
		}
	}
	return nil
}

func deleteImages(hub *registry.Registry, images []string) error {
	for _, v := range images {
		err := deleteImage(hub, v)
		if err != nil {
			return err
		}
	}
	return nil
}

func deleteImage(hub *registry.Registry, image string) error {
	tags, err := getTags(hub, image)
	if err != nil {
		return err
	}
	for _, v := range tags {
		err := deleteTag(hub, image, v)
		if err != nil {
			return err
		}
	}
	return nil
}

func tagsPrompt(hub *registry.Registry, image string) ([]string, error) {
	selectedTags := []string{}
	tags, err := getTags(hub, image)
	if err != nil {
		log.Fatalln(err)
		return nil, err
	}
	tags = append(tags, string(exitMenu))
	prompt := &survey.MultiSelect{
		Message: "Tags",
		Options: tags,
	}
	survey.AskOne(prompt, &selectedTags, survey.WithPageSize(22))
	return selectedTags, nil
}

func imagesPrompt(hub *registry.Registry) ([]string, error) {
	selectedImages := []string{}
	images, err := getImages(hub)
	if err != nil {
		log.Fatalln(err)
		return nil, err
	}
	images = append(images, string(exitMenu))
	prompt := &survey.MultiSelect{
		Message: "Images",
		Options: images,
	}

	survey.AskOne(prompt, &selectedImages, survey.WithPageSize(22))
	return selectedImages, nil
}

func singleActionPrompt(message string, actions []string) string {
	var action string
	prompt := &survey.Select{
		Message: message,
		Options: actions,
	}
	survey.AskOne(prompt, &action)
	return action
}

func passwordPrompt() string {
	password := ""
	prompt := &survey.Password{
		Message: "Please enter your password",
	}
	survey.AskOne(prompt, &password)
	return password
}

var usage = func() {
	desc := `Usage of registry-cleanup`

	fmt.Fprintf(os.Stderr, "%s\n\n", desc)
	fmt.Fprintf(os.Stderr, "Usage:\n")

	flag.PrintDefaults()
}

func main() {
	dryRun = new(bool)
	flag.Usage = usage
	address = flag.String("address", "http://localhost:5000", "docker registry URI")
	user = flag.String("user", "", "User for auth to docker registry, empty for anymous")

	if os.Getenv("DEBUG_REGISTRY_CLEANUP") == "1" {
		dryRun = flag.Bool("dryrun", false, "[DEBUG] dry run, don't acutally delete anything")
	}

	flag.Parse()

	url := *address
	username := *user
	password := ""
	if username != "" {
		password = passwordPrompt()
	}

	for {
		hub, err := registry.New(url, username, password)
		if err != nil {
			log.Println("Error connecting to server. Check arguments.")
			log.Println("Error response", err)
			os.Exit(1)
		}

		selectedImages, _ := imagesPrompt(hub)
		if contains(selectedImages, string(exitMenu)) {
			fmt.Println("Don't forget to cleanup your docker registry for the deleted tags.")
			fmt.Println("$ bin/registry garbage-collect /etc/docker/registry/config.yml")
			fmt.Println("\nDeleting a complete image does result in deleting all it's tags.")
			fmt.Println("If you deleted complete images you need to manually delete the residues")
			fmt.Println("in your docker registry filesystem. e.g. '/var/lib/registry/'")
			os.Exit(0)
		}
		fmt.Println(selectedImages)
		if len(selectedImages) == 1 { // only one images selected
			imagesAction := singleActionPrompt("Images", []string{"Delete", "Tags", "Back"})
			if imagesAction == "Delete" {
				yesno := singleActionPrompt("Really delete image '"+selectedImages[0]+"'?", []string{"Yes", "No"})
				if yesno == "Yes" {
					deleteImage(hub, selectedImages[0])
				}
			} else if imagesAction == "Tags" {
				for {
					selectedTags, _ := tagsPrompt(hub, selectedImages[0])
					if contains(selectedTags, string(exitMenu)) {
						break
					}
					fmt.Println(selectedTags)
					if len(selectedTags) > 0 {
						for {
							tagsaction := singleActionPrompt("Tags", []string{"Delete", "Back"})
							if tagsaction == "Delete" {
								yesno := singleActionPrompt("Really delete selected tags?", []string{"Yes", "No"})
								if yesno == "Yes" {
									fmt.Println("TODO: Deleting tags: ", selectedTags, " for image ", selectedImages[0])
									deleteTags(hub, selectedImages[0], selectedTags)
								}
								break
							} else if tagsaction == "Back" {
								break
							}
						}
					}
				}
			} else {
				break
			}
		} else if len(selectedImages) > 1 { // multiple images selected
			imagesAction := singleActionPrompt("Images", []string{"Delete", "Back"})
			if imagesAction == "Delete" {
				fmt.Println("Selected images: ", selectedImages)
				yesno := singleActionPrompt("Really delete selected images?", []string{"Yes", "No"})
				if yesno == "Yes" {
					fmt.Println("TODO: Deleting images: ", selectedImages)
					deleteImages(hub, selectedImages)
				}
			}
		}
	}
}

func contains(slice []string, item string) bool {
	set := make(map[string]struct{}, len(slice))
	for _, s := range slice {
		set[s] = struct{}{}
	}

	_, ok := set[item]
	return ok
}
