# Why Rust?

I chose Rust for the bonus implementation to show what compiled languages can do compared to Python.

## Main Reasons

**Performance**: Rust is fast. Like really fast. It compiles to native machine code and has no garbage collector, so there are no random pauses during execution.

**Memory Safety**: Rust's ownership system catches memory bugs at compile time. No null pointers, no data races, no use-after-free. These are the bugs that cause security vulnerabilities in production.

**Single Binary**: The whole app compiles to one executable. No Python interpreter, no dependencies to install, just copy the file and run it.

**Small Footprint**: A Rust web service uses way less memory than Python. We're talking 3-8 MB vs 20-40 MB for basically the same thing.

**Community**: Rust has a wonderful community, that even created a separate awesome website - [растпобеда.рф](растпобеда.рф). Currently there are issues, but I contacted the maintainer and he's on it!

**Mascot**: I like Ferris the crab more than gopher or other mascots.

## Trade-offs

**Learning Curve**: Not gonna lie, Rust is hard at first. The ownership system takes time to understand and the compiler is strict about everything.

**Compile Time**: Every change requires recompilation. Python's instant feedback is much nicer during development.

**Smaller Ecosystem**: Python has more libraries and examples for most things.

## When to Use Rust

Good for:

- High-traffic services that need performance
- Containerized apps (smaller images = faster deploys)
- Anything running on resource-constrained hardware
- Services where security is critical

Python is better for:

- Quick prototypes
- Apps that need lots of third-party integrations
- Teams without Rust experience
- Things that don't have performance issues

## Comparison with Go

Go would've been easier to learn and faster to compile. But Rust has better performance and memory safety guarantees. For a learning project, Rust teaches more valuable concepts even if it's harder.

## Real World

Companies like Discord, Cloudflare, and AWS use Rust in production. Discord famously rewrote part of their backend in Rust and went from 10GB memory usage to 2GB. That's the kind of difference we're talking about.

For this lab, having both Python and Rust implementations shows the trade-offs clearly. Python for speed of development, Rust for speed of execution.
