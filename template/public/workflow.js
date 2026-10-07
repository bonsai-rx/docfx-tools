export default {
    createCodeContainer: function(path) {
        const wrap = document.createElement("pre");
        wrap.innerHTML =
            '<a class="btn border-0 code-action" href="#" title="Copy">'+
            '  <i class="bi bi-clipboard"></i>'+
            '</a>';
        const button = wrap.querySelector("a");
        button.addEventListener("click", (e) => {
            e.preventDefault();
            fetch(path).then(req => req.text()).then(contents => {
                navigator.clipboard.writeText(contents);
                this.setCopyAlert(button);
            });
        });
        return wrap;
    },
    setCopyAlert: function(element) {
        const copyIcon = element.querySelector("i");
        element.classList.add("link-success");
        copyIcon.classList.add("bi-check-lg");
        copyIcon.classList.remove("bi-clipboard");
        setTimeout(function() {
            copyIcon.classList.remove("bi-check-lg");
            copyIcon.classList.add("bi-clipboard");
            element.classList.remove("link-success");
        }, 1000);
    },
    textFill: { light: "#000", dark: "#eee" },
    dataPrefix: "data:image/svg+xml;charset=utf-8,",
    themedImages: [],
    getTheme: function() {
        return document.documentElement.getAttribute("data-bs-theme") ??
            (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    },
    themedSource: function(svg, theme) {
        const end = svg.lastIndexOf("</svg>");
        const style = `<style>text { fill: ${this.textFill[theme] ?? this.textFill.light}; }</style>`;
        return this.dataPrefix + encodeURIComponent(svg.slice(0, end) + style + svg.slice(end));
    },
    loadThemedImage: async function(img, path) {
        let svg;
        try {
            const response = await fetch(path);
            svg = response.ok ? await response.text() : "";
        } catch {
            svg = "";
        }
        if (svg.lastIndexOf("</svg>") < 0) {
            img.src = path;
            return;
        }
        this.themedImages.push(img);
        img.src = this.themedSource(svg, this.getTheme());
    },
    setImageTheme: function(img, theme) {
        const svg = decodeURIComponent(img.src.slice(this.dataPrefix.length));
        const start = svg.lastIndexOf("<style>text { fill:");
        const stop = svg.indexOf("</style>", start) + "</style>".length;
        img.src = this.themedSource(svg.slice(0, start) + svg.slice(stop), theme);
    },
    renderElement: function(element) {
        element.classList.add("hljs");
        const img = element.querySelector("img");
        const workflowPath = img.src;
        this.loadThemedImage(img, workflowPath.replace(/\.[^.]+$/, ".svg"));

        const wrap = this.createCodeContainer(workflowPath);
        const parent = element.parentElement;
        parent.insertBefore(wrap, element);
        wrap.appendChild(element);
    },
    init: async function() {
        new MutationObserver(() => {
            const theme = this.getTheme();
            for (const image of this.themedImages) {
                this.setImageTheme(image, theme);
            }
        }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] })
        for (const element of document.getElementsByClassName("workflow")) {
            this.renderElement(element)
        }
    }
}