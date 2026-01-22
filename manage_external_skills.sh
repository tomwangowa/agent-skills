#!/bin/bash
# Script to manage external skill symlinks
# Usage: ./manage_external_skills.sh [link|unlink|status]

SKILLS_DIR="$HOME/.claude/skills"
SUPERPOWERS_DIR="$HOME/Development/3rdparty/superpowers/skills"
PREFIX="sp-"

link_skills() {
    echo "Creating symlinks for superpowers skills..."
    cd "$SKILLS_DIR" || exit 1

    if [ ! -d "$SUPERPOWERS_DIR" ]; then
        echo "Error: Superpowers directory not found at $SUPERPOWERS_DIR"
        exit 1
    fi

    for skill_path in "$SUPERPOWERS_DIR"/*; do
        if [ -d "$skill_path" ]; then
            skill_name=$(basename "$skill_path")
            link_name="${PREFIX}${skill_name}"

            if [ -e "$link_name" ]; then
                echo "  ⚠️  $link_name already exists, skipping"
            else
                ln -s "$skill_path" "$link_name"
                echo "  ✓ Linked: $link_name -> $skill_path"
            fi
        fi
    done
    echo "Done!"
}

unlink_skills() {
    echo "Removing superpowers skill symlinks..."
    cd "$SKILLS_DIR" || exit 1

    for link in ${PREFIX}*; do
        if [ -L "$link" ]; then
            rm "$link"
            echo "  ✓ Removed: $link"
        fi
    done
    echo "Done!"
}

status_skills() {
    echo "Status of external skills:"
    cd "$SKILLS_DIR" || exit 1

    echo -e "\nSuperpowers skills (${PREFIX}*):"
    for link in ${PREFIX}*; do
        if [ -L "$link" ]; then
            target=$(readlink "$link")
            if [ -e "$target" ]; then
                echo "  ✓ $link -> $target"
            else
                echo "  ✗ $link -> $target (broken link)"
            fi
        fi
    done
}

case "$1" in
    link)
        link_skills
        ;;
    unlink)
        unlink_skills
        ;;
    status)
        status_skills
        ;;
    *)
        echo "Usage: $0 {link|unlink|status}"
        echo ""
        echo "  link    - Create symlinks for all superpowers skills"
        echo "  unlink  - Remove all superpowers skill symlinks"
        echo "  status  - Show status of external skill links"
        exit 1
        ;;
esac
