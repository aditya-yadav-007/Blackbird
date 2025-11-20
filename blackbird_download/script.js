const outputElement = document.getElementById("output");
const typed = document.getElementById("typed");
const cursor = document.getElementById("cursor");
const hiddenInput = document.getElementById("hidden-input");

let buffer = "";



const banner = (`
============================================================
 $$$$$$\\        $$\\ $$\\   $$\\                        
$$  __$$\\       $$ |\\__|  $$ |                             
$$ /  $$ | $$$$$$$ |$$\\ $$$$$$\\   $$\\   $$\\  $$$$$$\\ 
$$$$$$$$ |$$  __$$ |$$ |\\_$$  _|  $$ |  $$ | \\____$$\\  
$$  __$$ |$$ /  $$ |$$ |  $$ |    $$ |  $$ | $$$$$$$ |     
$$ |  $$ |$$ |  $$ |$$ |  $$ |$$\\ $$ |  $$ |$$  __$$ |   
$$ |  $$ |\\$$$$$$$ |$$ |  \\$$$$  |\\$$$$$$$ |\\$$$$$$$ |     
\\__|  \\__| \\_______|\\__|   \\____/  \\____$$ | \\_______|      
                                  $$\\   $$ |      
                                  \\$$$$$$  | 
                                   \\______/  
------------------------------------------------------------
     Welcome to my Interactive Terminal
     Type 'help' to view available commands.
============================================================
`);

printOutput(banner);

const commands = 
{
  ls: "Access denied",
  sudo : "F*** Off",
  about: "This is a terminal-style website built using HTML, CSS, and JS.",
  pwd: "/home/usr/guest",
  exit: "Click on the X on the top right of the browser to exit",
  education: "$ Class 12th from ISC = 84%",
  email : "Contact me at aditya.ry2007@gmail.com",
  certifications: "$ Introduction to Cybersecurity - Cisco \n$ Computer Hardware Basics - Cisco",
  repo: "",
  github: "https://github.com/aditya-yadav-007",
  linkedin: "https://www.linkedin.com/in/aditya-r-yadav/",
  orcid: "ORCiD = 0009-0004-0622-706X",
  whoami: "Guest User"

};

const help = "Available commands: \n\ $ help \n\ $ help [command] - for more detailed info \n\ $ clear \n\ $ exit \n\ $ date \n\ $ echo \n\ $ curl \n\ $ pwd \n\ $ whoami \n\ $ about \n\ $ repo \n\ $ skills \n\ $ projects \n\ $ eductaion \n\ $ experience \n\ $ github \n\ $ email \n\ $ linkedin \n\ $ orcid \n\ (Don't add $)";
const helpDetails = {
  skills: "Lists core technical and creative skills.",
  about: "Displays information about the purpose of this terminal.",
  exit: "Helps you exit this page",
  date: "Shows Date and Time",
  clear: "clear — Clears all text from the terminal screen.",
  help: "Seriously ??!!! 😑",
  echo: "echo [text] - prints the \" text\" ",
  curl: "idk, try and find out \n\ curl [link \\ ip]",
  pwd: "Prints working directory",
  whoami: "🤐",
  repo: "Github Repostiry of the Website",
  projects: "Projects that I have worked on",
  education: "My education",
  github: "My GitHub Profile",
  email: "My email",
  linkedin: "My LinkedIn",
  orcid: "My ORCId",
};


// Output helper
function printOutput(text) {
  outputElement.innerHTML += text + "\n";
  outputElement.scrollTop = outputElement.scrollHeight;
}

function handleCommand(input) 
{
  const cmd = input.trim();
  if (!cmd) return;
  // Show prompt + typed command
  printOutput(`<span style="color:#90ee90;">user@guest&gt$ </span><span style="color:white;">${cmd}</span>\n`);

  const parts = cmd.toLowerCase().split(" ");
  const base = parts[0];
  const arg = parts[1];


  if (base === "clear") 
  {
    outputElement.innerHTML = "";
    printOutput(banner);
  }
  else if(base === "echo")
  {
    printOutput(arg + "\n" );
  }
  else if (base === "help") 
  {
    if (arg) 
    {
      if (helpDetails[arg]) 
        {
          printOutput(helpDetails[arg] + "\n");
        }
      else 
        {
        printOutput(`No detailed help found for '${arg}'.\n`);  
        }
    }
    else
      {
        printOutput(help+"\n");
      }
    
  } 
  else if (base === "curl") 
      {
    if (!arg) {
      printOutput("Usage: curl [url]\n");
    } else {
      printOutput(`Connecting to ${arg} ...\n`);
      setTimeout(() => {
        printOutput(`Connected to ${arg}\n`);
        printOutput(`HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 2048
Server: Aether-Terminal\n`);
        printOutput(`<html>
  <head><title>${arg}</title></head>
  <body><h1>Welcome to ${arg}</h1><p>This is a simulated curl response.</p></body>
</html>\n`);
      }, 800);
    }
  } 

  else if (base === "banner")
  {
    printOutput(banner);
  }

  else if (base === "date") 
  {
  const now = new Date();
  const formatted = now.toLocaleString(); // e.g. "10/22/2025, 4:35:10 PM"
  printOutput(`${formatted}\n`);
  }
  else if (base === "skills") 
  {
    printOutput("Opening detailed skills page...\n");
    window.open("./skills/index.html", "_blank"); // <-- change URL here
  }
  else if (base === "projects") 
  {
    printOutput("Opening detailed projects page...\n");
    window.open("./projects/index.html", "_blank"); // <-- change URL here
  }
  else if (base === "vim") 
  {
    printOutput("Not here buddy\n");
    window.open("https://www.vim.org/", "_blank"); // <-- change URL here
  }
  else if (commands[base]) 
  {
    printOutput(commands[base] + "\n");
  } 
  else 
  {
    printOutput("Command not found. Type \"help\" for list.\n");
  }
}


// Update typed text from hidden input
hiddenInput.addEventListener("input", () => {
  buffer = hiddenInput.value;
  typed.textContent = buffer;
});

// Submit on Enter
hiddenInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    handleCommand(buffer);
    buffer = "";
    typed.textContent = "";
    hiddenInput.value = "";
    e.preventDefault();
  }
});

// Focus the hidden input when terminal is tapped
document.getElementById("terminal").addEventListener("click", () => hiddenInput.focus());
window.onload = () => hiddenInput.focus();
