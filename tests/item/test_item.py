from typing import Dict

from stashofexile import gamedata
from stashofexile.items import item as m_item, socket as m_socket

ItemDict = Dict[str, m_item.Item]


def test_category(example_items: ItemDict):
    """
    Tests whether the order of test data matches the category order.
    Ensures that future tests work properly, since they retrieve an item using the index
    of its type.
    """

    for cat, item in example_items.items():
        assert item.category == cat


def test_tab_name(example_items: ItemDict):
    categories = gamedata.COMBO_ITEMS['Category']
    for i, cat in enumerate(categories):
        assert example_items[cat].tab == str(i)


def test_name_rarity(example_items: ItemDict):
    leaguestone = example_items['Leaguestone']
    assert leaguestone.name == 'Ambush Leaguestone'
    assert leaguestone.rarity == 'normal'

    sceptre = example_items['Sceptre']
    assert sceptre.name == 'Carnal Sceptre of the Apt'
    assert sceptre.rarity == 'magic'

    trinket = example_items['Trinket']
    assert trinket.name == 'Blight Relic, Thief\'s Trinket'
    assert trinket.rarity == 'rare'

    fishing_rod = example_items['Fishing Rod']
    assert fishing_rod.name == 'Reefbane, Fishing Rod'
    assert fishing_rod.rarity == 'unique'

    skill_gem = example_items['Skill Gem']
    assert skill_gem.name == 'Divergent Barrage'
    assert skill_gem.rarity == 'gem'

    currency = example_items['Currency']
    assert currency.name == 'Chaos Orb'
    assert currency.rarity == 'currency'

    divination_card = example_items['Divination Card']
    assert divination_card.name == 'Cartographer\'s Delight'
    assert divination_card.rarity == 'divination'

    quest = example_items['Quest']
    assert quest.name == 'Allflame'
    assert quest.rarity == 'quest'

    staff = example_items['Warstaff']
    assert staff.name == 'Pledge of Hands, Judgement Staff'
    assert staff.rarity == 'foil'


def test_dimensions(example_items: ItemDict):
    abyss_jewel = example_items['Abyss Jewel']
    assert abyss_jewel.width == 1
    assert abyss_jewel.height == 1

    omen = example_items['Omen']
    assert omen.width == 1
    assert omen.height == 1

    tattoo = example_items['Tattoo']
    assert tattoo.width == 1
    assert tattoo.height == 1

    rune_dagger = example_items['Rune Dagger']
    assert rune_dagger.width == 1
    assert rune_dagger.height == 3


def test_influences(example_items: ItemDict):
    amulet = example_items['Amulet']
    assert set(amulet.influences) == set(gamedata.INFLUENCES)

    helmet = example_items['Helmet']
    assert set(helmet.influences) == {'shaper', 'elder'}

    cluster_jewel = example_items['Cluster Jewel']
    assert cluster_jewel.influences == []


def test_property(example_items: ItemDict):
    oh_axe = example_items['One Handed Axe']
    assert [prop.description for prop in oh_axe.props] == [
        '<span style="color:#777777">One Handed Axe</span>',
        '<span style="color:#777777">Physical Damage: </span><span '
        'style="color:#8888ff">49-84</span>',
        '<span style="color:#777777">Critical Strike Chance: </span><span '
        'style="color:#ffffff">5.00%</span>',
        '<span style="color:#777777">Attacks per Second: </span><span '
        'style="color:#ffffff">1.30</span>',
        '<span style="color:#777777">Weapon Range: </span><span '
        'style="color:#ffffff">11</span>',
    ]

    resonator = example_items['Resonator']
    assert [prop.description for prop in resonator.props] == [
        '<span style="color:#777777">Stack Size: </span><span '
        'style="color:#ffffff">5/10</span>',
        '<span style="color:#777777">Requires <span style="color:#ac0100">3</span> '
        'Socketed Fossils</span>',
    ]

    blueprint = example_items['Blueprint']
    assert [prop.description for prop in blueprint.props] == [
        '<span style="color:#777777">Heist Target: <span '
        'style="color:#ffffff">Unusual Gems</span></span>',
        '<span style="color:#777777">Area Level: </span><span '
        'style="color:#ffffff">35</span>',
        '<span style="color:#777777">Wings Revealed: </span><span '
        'style="color:#ffffff">1/2</span>',
        '<span style="color:#777777">Escape Routes Revealed: </span><span '
        'style="color:#ffffff">1/4</span>',
        '<span style="color:#777777">Reward Rooms Revealed: </span><span '
        'style="color:#ffffff">1/6</span>',
        '<span style="color:#777777">Requires <span style="color:#ffffff">Brute '
        'Force</span> (Level <span style="color:#ffffff">1</span>)</span>',
        '<span style="color:#777777">Requires <span style="color:#ffffff">Trap '
        'Disarmament</span> (Level <span style="color:#ffffff">1</span>)</span>',
        '<span style="color:#777777">Requires <span '
        'style="color:#ffffff">Engineering</span> (Level <span '
        'style="color:#ffffff">1</span>)</span>',
        '<span style="color:#777777">Item Quantity: </span><span '
        'style="color:#8888ff">+61%</span>',
        '<span style="color:#777777">Item Rarity: </span><span '
        'style="color:#8888ff">+36%</span>',
        '<span style="color:#777777">Alert Level Reduction: </span><span '
        'style="color:#8888ff">+23%</span>',
        '<span style="color:#777777">Time Before Lockdown: </span><span '
        'style="color:#8888ff">+23%</span>',
        '<span style="color:#777777">Maximum Alive Reinforcements: </span><span '
        'style="color:#8888ff">+23%</span>',
    ]

    sanctum_research = example_items['Sanctum Research']
    assert [prop.description for prop in sanctum_research.props] == [
        '<span style="color:#777777">Area Level: </span><span style="color:#ffffff">83</span>',
        '<span style="color:#777777">Resolve: <span style="color:#ffffff">108</span>/<span style="color:#8888ff">108</span></span>',
        '<span style="color:#777777">Inspiration: <span style="color:#ffffff">51</span></span>',
        '<span style="color:#777777">Aureus: <span style="color:#ffffff">1045</span></span>',
        '<span style="color:#777777">Major Boons: </span><span style="color:#b5a890">Crystal Chalice</span>',
        '<span style="color:#777777">Minor Afflictions: </span><span style="color:#a06dca">Weakened Flesh</span>',
    ]


def test_property_function(example_items: ItemDict):
    bow = example_items['Bow']
    assert m_item.property_function('Quality')(bow) == '+48%'
    assert m_item.property_function('Attacks per Second')(bow) == '1.61'

    incubator = example_items['Incubator']
    assert m_item.property_function('Stack Size')(incubator) == '2/10'

    skill_gem = example_items['Skill Gem']
    assert m_item.property_function('Level')(skill_gem) == '21 (Max)'


def test_requirement(example_items: ItemDict):
    bow = example_items['Bow']
    assert [req.description for req in bow.reqs] == [
        '<span style="color:#777777">Level</span> <span '
        'style="color:#ffffff">82</span>',
        '<span style="color:#ffffff">111</span> <span '
        'style="color:#777777">Str</span>',
        '<span style="color:#ffffff">212</span> <span '
        'style="color:#777777">Dex</span>',
        '<span style="color:#ffffff">56</span> <span style="color:#777777">Int</span>',
    ]


def test_socket():
    socket_group: m_socket.SocketGroup = [
        m_socket.Socket.R,
        m_socket.Socket.G,
        m_socket.Socket.B,
        m_socket.Socket.A,
        m_socket.Socket.W,
        m_socket.Socket.DV,
    ]
    assert m_socket.format_socket_group(socket_group) == 'R-G-B-A-W-DV'


def test_sock_props(example_items: ItemDict):
    oh_sword = example_items['One Handed Sword']
    assert oh_sword.socket_groups == [
        [m_socket.Socket.B],
        [m_socket.Socket.G],
        [m_socket.Socket.R],
    ]
    assert oh_sword.sockets == [m_socket.Socket.B, m_socket.Socket.G, m_socket.Socket.R]
    assert oh_sword.sockets_b == 1
    assert oh_sword.sockets_g == 1
    assert oh_sword.sockets_r == 1
    assert oh_sword.num_sockets == 3
    assert oh_sword.num_links == 1
    assert oh_sword.has_sockets()

    oh_mace = example_items['One Handed Mace']
    assert oh_mace.socket_groups == [
        [m_socket.Socket.B, m_socket.Socket.B, m_socket.Socket.W]
    ]
    assert oh_mace.sockets == [m_socket.Socket.B, m_socket.Socket.B, m_socket.Socket.W]
    assert oh_mace.sockets_b == 2
    assert oh_mace.sockets_w == 1
    assert oh_mace.num_sockets == 3
    assert oh_mace.num_links == 3
    assert oh_mace.has_sockets()

    resonator = example_items['Resonator']
    assert resonator.socket_groups == [
        [m_socket.Socket.DV],
        [m_socket.Socket.DV],
        [m_socket.Socket.DV],
    ]
    assert resonator.sockets == [
        m_socket.Socket.DV,
        m_socket.Socket.DV,
        m_socket.Socket.DV,
    ]
    assert resonator.num_sockets == 3
    assert resonator.num_links == 1
    assert resonator.has_sockets()


def test_wep_props(example_items: ItemDict):
    staff = example_items['Staff']
    assert staff.damage == 576.0
    assert staff.aps == 1.15
    assert staff.crit == 6.5
    assert staff.dps == 662.4
    assert staff.pdps == 110.975
    assert staff.edps == 551.425

    warstaff = example_items['Warstaff']
    assert warstaff.damage == 136.0
    assert warstaff.aps == 1.3
    assert warstaff.crit == 6.5
    assert warstaff.dps == 176.8
    assert warstaff.pdps == 176.8


def test_arm_props(example_items: ItemDict):
    shield = example_items['Shield']
    assert shield.armour == 533
    assert shield.energy_shield == 108
    assert shield.block == 32

    gloves = example_items['Gloves']
    assert gloves.evasion == 131

    boots = example_items['Boots']
    assert boots.ward == 294


def test_req_props(example_items: ItemDict):
    th_axe = example_items['Two Handed Axe']
    assert th_axe.req_level == 72
    assert th_axe.req_str == 159
    assert th_axe.req_dex == 76
    assert th_axe.req_int == 46

    jewel = example_items['Jewel']
    assert jewel.req_class == 'Ranger'


def test_gem_props(example_items: ItemDict):
    skill_gem = example_items['Skill Gem']
    assert skill_gem.gem_lvl == 21
    assert skill_gem.current_exp is None
    assert skill_gem.max_exp is None
    assert skill_gem.gem_exp is None
    assert skill_gem.gem_quality == 'Divergent'

    support_gem = example_items['Support Gem']
    assert support_gem.gem_lvl == 12
    assert support_gem.current_exp == 162543
    assert support_gem.max_exp == 1956648
    assert support_gem.gem_exp == support_gem.current_exp / support_gem.max_exp * 100
    assert support_gem.gem_quality == 'Superior (Default)'


def test_ilvl(example_items: ItemDict):
    leaguestone = example_items['Leaguestone']
    assert leaguestone.ilvl == 45

    sentinel = example_items['Sentinel']
    assert sentinel.ilvl == 7

    incubator = example_items['Incubator']
    assert incubator.ilvl == 83

    beast = example_items['Captured Beast']
    assert beast.ilvl == 81

    metamorph = example_items['Metamorph Sample']
    assert metamorph.ilvl == 83


def test_misc_props(example_items: ItemDict):
    helmet = example_items['Helmet']
    assert helmet.split

    skill_gem = example_items['Skill Gem']
    assert skill_gem.corrupted

    dagger = example_items['Dagger']
    assert not dagger.identified

    th_mace = example_items['Two Handed Mace']
    assert th_mace.mirrored

    assert dagger.fractured_tag

    quiver = example_items['Quiver']
    assert quiver.synthesised

    boots = example_items['Boots']
    assert boots.searing
    assert boots.tangled

    sanctum_relic = example_items['Sanctum Relic']
    assert sanctum_relic.unmodifiable

    claw = example_items['Claw']
    assert claw.quality == '+30%'
    assert claw.quality_num == 30

    wand = example_items['Wand']
    assert wand.altart

    th_sword = example_items['Two Handed Sword']
    assert th_sword.crafted_tag

    assert th_mace.veiled_tag

    flask = example_items['Flask']
    assert flask.enchanted_tag

    body_armour = example_items['Body Armour']
    assert body_armour.scourge_tier == 3

    assert flask.cosmetic_tag

    assert not claw.split
    assert not claw.corrupted
    assert claw.identified
    assert not claw.mirrored
    assert not claw.fractured_tag
    assert not claw.synthesised
    assert not claw.searing
    assert not claw.tangled
    assert not claw.unmodifiable
    assert not claw.altart
    assert not claw.crafted_tag
    assert not claw.veiled_tag
    assert not claw.enchanted_tag
    assert claw.scourge_tier == 0
    assert not claw.cosmetic_tag


def test_mods(example_items: ItemDict):
    logbook = example_items['Expedition Logbook']
    assert logbook.logbook == [
        {
            'faction': {'id': 'Faction1', 'name': 'Druids of the Broken Circle'},
            'mods': [
                '29% increased number of Explosives',
                'Area contains 31% increased number of Monster Markers',
            ],
            'name': 'Volcanic Island',
        },
        {
            'faction': {'id': 'Faction1', 'name': 'Druids of the Broken Circle'},
            'mods': [
                '12% increased quantity of Artifacts dropped by Monsters',
                'Area contains 24% increased number of Monster Markers',
            ],
            'name': 'Shipwreck Reef',
        },
    ]

    ring = example_items['Ring']
    assert ring.implicit == ['Adds 4 to 14 Physical Damage to Attacks']

    body_armour = example_items['Body Armour']
    assert body_armour.scourge == [
        'Regenerate 26 Life per second',
        '25% reduced Global Defences',
    ]

    flask = example_items['Flask']
    assert flask.utility == [
        '+50% to Lightning Resistance',
        '20% less Lightning Damage taken',
    ]

    map_item = example_items['Map']
    assert map_item.fractured == [
        'Slaying Enemies close together has a 13% chance to attract monsters from Beyond'
    ]

    assert map_item.explicit == [
        'Area is inhabited by ranged monsters',
        'Players are Cursed with Enfeeble',
        '25% more Monster Life',
        'Monsters cannot be Stunned',
    ]

    th_sword = example_items['Two Handed Sword']
    assert th_sword.crafted == [
        'Can have up to 3 Crafted Modifiers',
        'Adds 22 to 39 Physical Damage',
        '25% increased Critical Strike Chance',
        '+17% to Quality',
    ]

    th_mace = example_items['Two Handed Mace']
    assert th_mace.veiled == ['Veiled Suffix']

    assert map_item.enchanted == [
        'Does not consume Sextant Uses',
        'Delirium Reward Type: Scarabs',
        'Delirium Reward Type: Scarabs',
        'Delirium Reward Type: Scarabs',
        'Delirium Reward Type: Scarabs',
        'Delirium Reward Type: Scarabs',
        'Players in Area are 100% Delirious',
    ]

    assert th_sword.cosmetic == [
        'Has Voidforge Skin. You can reclaim this by shift-clicking this item.'
    ]

    assert body_armour.incubator == {
        'level': 68,
        'name': 'Shaper or Elder Armour Item',
        'progress': 0,
        'total': 14854,
    }

    skill_gem = example_items['Skill Gem']
    assert skill_gem.gem == (
        'After a short preparation time, you attack repeatedly with a ranged weapon. '
        'These attacks have a small randomised spread. Only works with Bows and Wands.'
    )

    unique_fragment = example_items['Unique Fragment']
    assert unique_fragment.logbook == []
    assert unique_fragment.implicit == []
    assert unique_fragment.scourge == []
    assert unique_fragment.utility == []
    assert unique_fragment.fractured == []
    assert unique_fragment.explicit == []
    assert unique_fragment.crafted == []
    assert unique_fragment.veiled == []
    assert unique_fragment.enchanted == []
    assert unique_fragment.cosmetic == []
    assert unique_fragment.incubator is None
    assert unique_fragment.gem is None


def test_image(example_items: ItemDict):
    pass


def test_tooltip(example_items: ItemDict):
    pass


def test_text(example_items: ItemDict):
    pass
