module defi_suite::token {
    use std::signer;
    use std::string::{String, utf8};
    use aptos_framework::fungible_asset::{Self, MintRef, TransferRef, BurnRef, Metadata};
    use aptos_framework::object::{Self, Object};
    use aptos_framework::primary_fungible_store;

    /// Error codes
    const E_NOT_OWNER: u64 = 1;
    const E_INSUFFICIENT_BALANCE: u64 = 2;

    /// Resource that stores the token refs for management
    // currently unlimited supply 
    struct TokenRefs has key {
        mint_ref: MintRef, // creator mint new tokens.
        transfer_ref: TransferRef, // moving tokens b/w accounts
        burn_ref: BurnRef, // burning tokens 
    }

    /// Create a new fungible token
// create_token
// Called once to initialize a new token.
// Steps:
    // Creates a named object representing the token.
    // Calls create_primary_store_enabled_fungible_asset to register metadata:
    // name, symbol, decimals, icon_uri, project_uri
    // Generates mint/transfer/burn capabilities.
    // Stores them under the creator’s account.
    // Optionally mints an initial_supply and deposits it to the creator.
    public entry fun create_token(
        creator: &signer,
        name: vector<u8>,
        symbol: vector<u8>,
        decimals: u8,
        initial_supply: u64,
        icon_uri: vector<u8>,
        project_uri: vector<u8>,
    ) {
        let constructor_ref = object::create_named_object(creator, name);
        
        primary_fungible_store::create_primary_store_enabled_fungible_asset(
            &constructor_ref,
            option::none(),
            utf8(name),
            utf8(symbol),
            decimals,
            utf8(icon_uri),
            utf8(project_uri),
        );

        let mint_ref = fungible_asset::generate_mint_ref(&constructor_ref);
        let transfer_ref = fungible_asset::generate_transfer_ref(&constructor_ref);
        let burn_ref = fungible_asset::generate_burn_ref(&constructor_ref);
        
        // Store refs for later use
        move_to(creator, TokenRefs {
            mint_ref,
            transfer_ref,
            burn_ref,
        });

        // Mint initial supply to creator
        if (initial_supply > 0) {
            let metadata = object::object_from_constructor_ref<Metadata>(&constructor_ref);
            let fa = fungible_asset::mint(&mint_ref, initial_supply);
            primary_fungible_store::deposit(signer::address_of(creator), fa);
        };
    }

    /// Mint tokens to a specific address (only token creator)
    public entry fun mint(
        creator: &signer,
        to: address,
        amount: u64
    ) acquires TokenRefs {
        let creator_addr = signer::address_of(creator);
        assert!(exists<TokenRefs>(creator_addr), E_NOT_OWNER);
        
        let token_refs = borrow_global<TokenRefs>(creator_addr);
        let fa = fungible_asset::mint(&token_refs.mint_ref, amount);
        primary_fungible_store::deposit(to, fa);
    }

    /// Burn tokens from creator's account
    public entry fun burn(
        creator: &signer,
        amount: u64
    ) acquires TokenRefs {
        let creator_addr = signer::address_of(creator);
        assert!(exists<TokenRefs>(creator_addr), E_NOT_OWNER);
        
        let token_refs = borrow_global<TokenRefs>(creator_addr);
        let fa = primary_fungible_store::withdraw(creator, amount);
        fungible_asset::burn(&token_refs.burn_ref, fa);
    }
}
